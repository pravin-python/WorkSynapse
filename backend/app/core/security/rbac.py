"""
WorkSynapse RBAC (Role-Based Access Control) Module
====================================================
Consolidated RBAC decorators, checkers, and permission utilities.

Security Features:
- Permission-based access control
- Role-based access control
- Superuser bypass
- Security event logging
"""
from typing import Any, Callable, List, Optional, Set
from functools import wraps
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")


def require_permission(resource: str, action):
    """
    Decorator to require a specific permission for an endpoint.
    
    Usage:
        from app.models.user.model import PermissionAction
        
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
        from app.models.user.model import PermissionAction
        
        @router.get("/projects/{project_id}")
        async def get_project(
            project_id: int,
            _: None = Depends(RBACChecker(resource="projects", action=PermissionAction.READ)),
            current_user: User = Depends(get_current_user)
        ):
            ...
    """
    def __init__(self, resource: str, action):
        self.resource = resource
        self.action = action
    
    async def __call__(
        self,
        current_user = None,
        db: AsyncSession = None,
    ):
        # Import here to avoid circular imports
        from app.core.security.deps import get_current_user
        from app.database.session import get_db
        
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if current_user.is_superuser:
            return True
        
        has_permission = current_user.has_permission(self.resource, self.action)
        
        if not has_permission:
            # Log security event
            if db:
                from app.models.worklog.model import SecurityAuditLog
                security_log = SecurityAuditLog(
                    event_type="permission_denied",
                    severity="MEDIUM",
                    user_id=current_user.id,
                    ip_address="unknown",
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
# PERMISSION HELPER FUNCTIONS
# =============================================================================

def check_permission(user, resource: str, action) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        user: User object
        resource: Resource name (e.g., "projects", "tasks")
        action: PermissionAction enum value
        
    Returns:
        bool: True if user has permission
    """
    if user.is_superuser:
        return True
    return user.has_permission(resource, action)


def check_any_role(user, *roles: str) -> bool:
    """
    Check if a user has any of the specified roles.
    
    Args:
        user: User object
        *roles: Role names to check
        
    Returns:
        bool: True if user has any of the roles
    """
    if user.is_superuser:
        return True
    
    user_role_names = {role.name for role in user.roles}
    user_role_names.add(user.role.value)
    
    return any(role in user_role_names for role in roles)


def check_all_roles(user, *roles: str) -> bool:
    """
    Check if a user has all of the specified roles.
    
    Args:
        user: User object
        *roles: Role names to check
        
    Returns:
        bool: True if user has all of the roles
    """
    if user.is_superuser:
        return True
    
    user_role_names = {role.name for role in user.roles}
    user_role_names.add(user.role.value)
    
    return all(role in user_role_names for role in roles)
