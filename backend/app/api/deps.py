"""
Authentication Dependencies - RBAC and Token Verification
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status, WebSocket, Query
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.core.security import decode_token, TokenPayload
from app.models.user.model import User, UserRole
from app.services.user import user_service
from app.core.logging import security_logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None or payload.type != "access":
        raise credentials_exception
    
    user = await user_service.get(db, id=int(payload.sub))
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verify user is active superuser."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user

def require_roles(allowed_roles: List[UserRole]):
    """Role-based access control dependency factory."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.is_superuser:
            return current_user
            
        if current_user.role not in allowed_roles:
            security_logger.log_permission_denied(
                user_id=str(current_user.id),
                resource="endpoint",
                action="access"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Common role requirements
require_admin = require_roles([UserRole.ADMIN])
require_manager = require_roles([UserRole.ADMIN, UserRole.MANAGER])
require_developer = require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.DEVELOPER])

async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Authenticate WebSocket connections via query param token."""
    if not token:
        await websocket.close(code=4001)
        return None
    
    payload = decode_token(token)
    if payload is None or payload.type != "access":
        await websocket.close(code=4001)
        return None
    
    user = await user_service.get(db, id=int(payload.sub))
    if user is None or not user.is_active:
        await websocket.close(code=4001)
        return None
    
    return user

async def verify_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Verify API key for service-to-service communication."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required"
        )
    # Implement actual API key verification logic here
    return True
