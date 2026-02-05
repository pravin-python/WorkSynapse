"""
WorkSynapse Security Dependencies
=================================
FastAPI dependencies for authentication and authorization.

These are the primary entry points for securing endpoints.
"""
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from pydantic import BaseModel
import datetime
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")

# JWT Bearer auth scheme
bearer_scheme = HTTPBearer(auto_error=False)


# =============================================================================
# TOKEN DATA MODEL
# =============================================================================

class TokenData(BaseModel):
    """JWT token payload data."""
    user_id: int
    email: str
    exp: datetime.datetime
    jti: str  # JWT ID for token revocation


# =============================================================================
# TOKEN OPERATIONS
# =============================================================================

def create_access_token(
    user,
    expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user: User object with id and email
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT token
    """
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
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData if valid, None otherwise
    """
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
# AUTHENTICATION DEPENDENCIES
# =============================================================================

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = None,
):
    """
    Get the current authenticated user from JWT token.
    
    This is the primary authentication dependency.
    
    Raises:
        HTTPException: If not authenticated or user is invalid
    """
    # Import here to avoid circular imports
    from app.database.session import get_db
    from app.services.user import user_service
    
    # Get DB session if not provided
    if db is None:
        async for session in get_db():
            db = session
            break
    
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
    if hasattr(user, 'is_locked') and user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is locked"
        )
    
    return user


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = None,
):
    """
    Get the current user if authenticated, otherwise None.
    
    Use this for endpoints that work differently for authenticated vs anonymous users.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


async def get_current_active_superuser(
    current_user = Depends(get_current_user),
):
    """
    Get the current user and verify they are a superuser.
    
    Use this for admin-only endpoints.
    
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required"
        )
    return current_user


# =============================================================================
# REQUEST CONTEXT UTILITIES
# =============================================================================

def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Handles forwarded headers for proxy deployments.
    """
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
