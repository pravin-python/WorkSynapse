"""
Auth Router - Login, Token Refresh, Logout
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.database.session import get_db
from app.services.user import user as user_service
from app.core.security import (
    verify_password,
    create_token_pair,
    verify_token_type,
    get_password_hash,
    TokenPair
)
from app.core.logging import security_logger
from app.api.deps import get_current_user
from app.models.user.model import User

router = APIRouter()

class LoginResponse(TokenPair):
    user_id: int
    email: str
    role: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """OAuth2 compatible login endpoint."""
    client_ip = request.client.host if request.client else "unknown"
    
    user = await user_service.get_by_email(db, email=form_data.username)
    if not user:
        security_logger.log_auth_failure(form_data.username, client_ip, "User not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        security_logger.log_auth_failure(form_data.username, client_ip, "Invalid password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        security_logger.log_auth_failure(form_data.username, client_ip, "Inactive user")
        raise HTTPException(status_code=400, detail="Inactive user")
    
    tokens = create_token_pair(str(user.id), user.role.value)
    security_logger.log_auth_success(str(user.id), client_ip)
    
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        user_id=user.id,
        email=user.email,
        role=user.role.value
    )

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
    
    from app.schemas.user import UserCreate
    from app.models.user.model import UserRole
    
    user_in = UserCreate(
        email=data.email,
        password=get_password_hash(data.password),
        full_name=data.full_name,
        role=UserRole.DEVELOPER
    )
    user = await user_service.create(db, obj_in=user_in)
    
    tokens = create_token_pair(str(user.id), user.role.value)
    security_logger.log_auth_success(str(user.id), client_ip)
    
    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        user_id=user.id,
        email=user.email,
        role=user.role.value
    )

@router.post("/refresh", response_model=TokenPair)
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
    
    return create_token_pair(str(user.id), user.role.value)

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard tokens)."""
    # In a production system, you'd add the token to a blacklist in Redis
    return {"message": "Successfully logged out"}
