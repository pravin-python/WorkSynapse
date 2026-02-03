"""
Security Module - JWT, Password Hashing, and Token Management
"""
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from app.core.config import settings

# Password Hashing Context (Argon2 preferred, bcrypt fallback)
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    iat: datetime
    type: str  # "access" or "refresh"
    role: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using argon2/bcrypt."""
    return pwd_context.hash(password)

def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "role": role
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(subject: str, role: str) -> str:
    """Create a JWT refresh token (longer lived)."""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "role": role
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_token_pair(subject: str, role: str) -> TokenPair:
    """Create both access and refresh tokens."""
    return TokenPair(
        access_token=create_access_token(subject, role),
        refresh_token=create_refresh_token(subject, role)
    )

def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None

def verify_token_type(token: str, expected_type: str) -> Optional[TokenPayload]:
    """Verify that a token is of the expected type."""
    payload = decode_token(token)
    if payload and payload.type == expected_type:
        return payload
    return None
