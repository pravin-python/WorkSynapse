"""
Auth Router - Login, Token Refresh, Logout
"""
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.database.session import get_db
from app.services.user import user_service
from app.core.security import (
    verify_password,
    create_token_pair,
    verify_token_type,
    get_password_hash,
    TokenPair
)
from app.core.logging import security_logger
from app.api.deps import get_current_user
from app.models.user.model import User, UserRole
from app.schemas.user import UserCreate

router = APIRouter()

# =============================================================================
# MODELS
# =============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class RefreshRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    roles: List[str]
    permissions: List[str]
    is_superuser: bool
    is_active: bool

class LoginResponse(TokenPair):
    user: UserResponse

# =============================================================================
# HELPERS
# =============================================================================

def build_login_response(user: User, tokens: TokenPair) -> LoginResponse:
    """Helper to construct the full login response with user details."""
    # Collect roles
    role_names = [r.name for r in user.roles]
    if user.role.value not in role_names:
        role_names.append(user.role.value)
    
    # Collect permissions
    permissions = set()
    for r in user.roles:
        for p in r.permissions:
            permissions.add(f"{p.resource}.{p.action.value}")
            
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        roles=role_names,
        permissions=list(permissions),
        is_superuser=user.is_superuser,
        is_active=user.is_active
    )
    
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        user=user_response
    )

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """OAuth2 compatible login endpoint."""
    client_ip = request.client.host if request.client else "unknown"
    
    user = await user_service.get_by_email(db, email=login_data.email)
    if not user:
        security_logger.log_auth_failure(login_data.email, client_ip, "User not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(login_data.password, user.hashed_password):
        security_logger.log_auth_failure(login_data.email, client_ip, "Invalid password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        security_logger.log_auth_failure(login_data.email, client_ip, "Inactive user")
        raise HTTPException(status_code=400, detail="Inactive user")
    
    tokens = create_token_pair(str(user.id), user.role.value)
    security_logger.log_auth_success(str(user.id), client_ip)
    
    return build_login_response(user, tokens)

@router.post("/register", response_model=LoginResponse)
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    client_ip = request.client.host if request.client else "unknown"
    
    existing = await user_service.get_by_email(db, email=data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_in = UserCreate(
        email=data.email,
        password=get_password_hash(data.password),
        full_name=data.full_name,
        role=UserRole.DEVELOPER
    )
    user = await user_service.create(db, obj_in=user_in)
    
    tokens = create_token_pair(str(user.id), user.role.value)
    security_logger.log_auth_success(str(user.id), client_ip)
    
    return build_login_response(user, tokens)

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    payload = verify_token_type(data.refresh_token, "refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = await user_service.get(db, id=int(payload.sub))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    tokens = create_token_pair(str(user.id), user.role.value)
    
    # Check if refresh token rotation is needed or just issue new access token
    # For now, we issue a new pair
    
    return build_login_response(user, tokens)

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard tokens)."""
    # In a production system, you'd add the token to a blacklist in Redis
    return {"message": "Successfully logged out"}
