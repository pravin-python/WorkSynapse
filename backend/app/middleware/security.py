"""
WorkSynapse Security Middleware & Decorators
=============================================
Security layer with RBAC, audit logging, and request validation.

Security Features:
- JWT authentication
- Role-based access control (RBAC)
- Request audit logging
- Rate limiting
- SQL injection protection
- Input sanitization
"""
from typing import Any, Callable, List, Optional, Set
from functools import wraps
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from pydantic import BaseModel
import datetime
import hashlib
import re
import logging

from app.core.config import settings
from app.database.session import get_db
from app.models.user.model import User, PermissionAction
from app.models.worklog.model import ActivityLog, ActivityType, SecurityAuditLog
from app.services.user import user_service

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")

# JWT Bearer auth
bearer_scheme = HTTPBearer(auto_error=False)


# =============================================================================
# TOKEN HANDLING
# =============================================================================

class TokenData(BaseModel):
    """JWT token payload."""
    user_id: int
    email: str
    exp: datetime.datetime
    jti: str  # JWT ID for token revocation


def create_access_token(
    user: User,
    expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """Create a JWT access token for a user."""
    import uuid
    
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "sub": str(user.id),
        "email": user.email,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        user_id = int(payload.get("sub"))
        email = payload.get("email")
        exp = datetime.datetime.fromtimestamp(payload.get("exp"), tz=datetime.timezone.utc)
        jti = payload.get("jti")
        
        if not all([user_id, email, exp, jti]):
            return None
        
        return TokenData(user_id=user_id, email=email, exp=exp, jti=jti)
    
    except JWTError:
        return None


# =============================================================================
# DEPENDENCY INJECTION - AUTHENTICATION
# =============================================================================

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Raises HTTPException if not authenticated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    token_data = decode_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    # Check token expiration
    if datetime.datetime.now(datetime.timezone.utc) > token_data.exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await user_service.get(db, token_data.user_id)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Check if user is locked
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is locked"
        )
    
    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise None.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current user and verify they are a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required"
        )
    return current_user


# =============================================================================
# RBAC DECORATORS
# =============================================================================

def require_permission(resource: str, action: PermissionAction):
    """
    Decorator to require a specific permission for an endpoint.
    
    Usage:
        @router.get("/projects")
        @require_permission("projects", PermissionAction.READ)
        async def list_projects(current_user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Superusers have all permissions
            if current_user.is_superuser:
                return await func(*args, **kwargs)
            
            # Check permission
            has_perm = current_user.has_permission(resource, action)
            if not has_perm:
                security_logger.warning(
                    f"Permission denied: user={current_user.id}, "
                    f"resource={resource}, action={action.value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {action.value} on {resource}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_roles(*roles: str):
    """
    Decorator to require specific roles for an endpoint.
    
    Usage:
        @router.delete("/users/{user_id}")
        @require_roles("ADMIN", "SUPER_ADMIN")
        async def delete_user(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Superusers bypass role checks
            if current_user.is_superuser:
                return await func(*args, **kwargs)
            
            # Check if user has any of the required roles
            user_role_names = {role.name for role in current_user.roles}
            user_role_names.add(current_user.role.value)  # Include legacy role
            
            if not any(role in user_role_names for role in roles):
                security_logger.warning(
                    f"Role denied: user={current_user.id}, "
                    f"required={roles}, has={user_role_names}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required roles: {', '.join(roles)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class RBACChecker:
    """
    Dependency class for checking RBAC permissions.
    
    Usage:
        @router.get("/projects/{project_id}")
        async def get_project(
            project_id: int,
            _: None = Depends(RBACChecker(resource="projects", action=PermissionAction.READ)),
            current_user: User = Depends(get_current_user)
        ):
            ...
    """
    def __init__(self, resource: str, action: PermissionAction):
        self.resource = resource
        self.action = action
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        if current_user.is_superuser:
            return True
        
        has_permission = current_user.has_permission(self.resource, self.action)
        
        if not has_permission:
            # Log security event
            security_log = SecurityAuditLog(
                event_type="permission_denied",
                severity="MEDIUM",
                user_id=current_user.id,
                ip_address="unknown",  # Would be extracted from request
                resource_type=self.resource,
                description=f"Permission denied: {self.action.value} on {self.resource}",
            )
            db.add(security_log)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {self.action.value} on {self.resource}"
            )
        
        return True


# =============================================================================
# INPUT VALIDATION & SANITIZATION
# =============================================================================

class InputSanitizer:
    """
    Sanitize user inputs to prevent XSS and injection attacks.
    """
    
    # Patterns to remove
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                  # JavaScript URLs
        r'on\w+\s*=',                   # Event handlers
        r'<iframe[^>]*>',               # Iframes
        r'<object[^>]*>',               # Object tags
        r'<embed[^>]*>',                # Embed tags
    ]
    
    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """Sanitize a string input."""
        if not value:
            return value
        
        sanitized = value
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # HTML entity encode special characters
        sanitized = sanitized.replace('<', '&lt;').replace('>', '&gt;')
        
        return sanitized.strip()
    
    @classmethod
    def sanitize_email(cls, email: str) -> str:
        """Validate and sanitize email."""
        email = email.lower().strip()
        
        # Basic email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email
    
    @classmethod
    def sanitize_url(cls, url: str) -> str:
        """Validate and sanitize URL."""
        url = url.strip()
        
        # Check for dangerous schemes
        if any(scheme in url.lower() for scheme in ['javascript:', 'data:', 'vbscript:']):
            raise ValueError("Invalid URL scheme")
        
        # Basic URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url, re.IGNORECASE):
            raise ValueError("Invalid URL format")
        
        return url


class SQLInjectionProtection:
    """
    Additional SQL injection protection utilities.
    
    Note: SQLAlchemy ORM already provides parameterized queries,
    but this adds extra validation for dynamic queries.
    """
    
    # SQL keywords that shouldn't appear in user input
    DANGEROUS_KEYWORDS = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE',
        'CREATE', 'ALTER', 'GRANT', 'REVOKE', 'UNION', 'OR 1=1',
        'OR 1 = 1', '--', '/*', '*/', 'EXEC', 'EXECUTE',
    ]
    
    @classmethod
    def is_safe_input(cls, value: str) -> bool:
        """Check if input is safe from SQL injection."""
        upper_value = value.upper()
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in upper_value:
                return False
        return True
    
    @classmethod
    def sanitize_identifier(cls, identifier: str) -> str:
        """
        Sanitize a database identifier (table/column name).
        
        Only allow alphanumeric and underscores.
        """
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)
        if not sanitized or sanitized[0].isdigit():
            raise ValueError("Invalid identifier")
        return sanitized


# =============================================================================
# AUDIT LOGGING MIDDLEWARE
# =============================================================================

class AuditLogger:
    """
    Log all significant actions for audit trail.
    """
    
    @staticmethod
    async def log_activity(
        db: AsyncSession,
        *,
        user_id: Optional[int],
        activity_type: ActivityType,
        resource_type: str,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        action: str,
        description: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
    ):
        """Log an activity to the audit trail."""
        activity = ActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            action=action,
            description=description,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
        )
        
        db.add(activity)
        await db.commit()
        
        logger.info(
            f"Activity logged: {activity_type.value} - {action}",
            extra={
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        )
    
    @staticmethod
    async def log_security_event(
        db: AsyncSession,
        *,
        event_type: str,
        severity: str,
        user_id: Optional[int] = None,
        email_attempted: Optional[str] = None,
        ip_address: str,
        user_agent: Optional[str] = None,
        description: str,
        details: Optional[dict] = None,
        action_taken: Optional[str] = None,
    ):
        """Log a security event."""
        security_event = SecurityAuditLog(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            email_attempted=email_attempted,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
            details=details,
            action_taken=action_taken,
        )
        
        db.add(security_event)
        await db.commit()
        
        security_logger.warning(
            f"Security event: {event_type} - {description}",
            extra={
                "severity": severity,
                "user_id": user_id,
                "ip_address": ip_address,
            }
        )


# =============================================================================
# REQUEST CONTEXT EXTRACTION
# =============================================================================

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for forwarded headers (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    if request.client:
        return request.client.host
    
    return "unknown"


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request."""
    return request.headers.get("User-Agent")


# =============================================================================
# RATE LIMITING HELPERS
# =============================================================================

def generate_rate_limit_key(identifier: str, action: str) -> str:
    """Generate a key for rate limiting."""
    return f"rate_limit:{action}:{hashlib.md5(identifier.encode()).hexdigest()}"
