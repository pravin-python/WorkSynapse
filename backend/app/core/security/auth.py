"""
Authentication & Token Management
=================================
Provides JWT token creation/validation and password hashing utilities.

Features:
- Argon2/bcrypt password hashing
- JWT access & refresh token creation
- Token validation and decoding
- Secure token pair generation
"""

from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from app.core.config import settings


# =============================================================================
# PASSWORD HASHING
# =============================================================================

# Password Hashing Context (Argon2 preferred, bcrypt fallback)
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using argon2/bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password string
    """
    return pwd_context.hash(password)


# =============================================================================
# TOKEN MODELS
# =============================================================================

class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str
    exp: datetime
    iat: datetime
    type: str  # "access" or "refresh"
    role: str


class TokenPair(BaseModel):
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# =============================================================================
# TOKEN CREATION
# =============================================================================

def create_access_token(
    subject: str, 
    role: str, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The token subject (usually user ID)
        role: User's role for authorization
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT access token string
    """
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
    """
    Create a JWT refresh token (longer lived).
    
    Args:
        subject: The token subject (usually user ID)
        role: User's role for authorization
        
    Returns:
        Encoded JWT refresh token string
    """
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
    """
    Create both access and refresh tokens.
    
    Args:
        subject: The token subject (usually user ID)
        role: User's role for authorization
        
    Returns:
        TokenPair containing both tokens
    """
    return TokenPair(
        access_token=create_access_token(subject, role),
        refresh_token=create_refresh_token(subject, role)
    )


# =============================================================================
# TOKEN VALIDATION
# =============================================================================

def decode_token(token: str) -> Optional[TokenPayload]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token string to decode
        
    Returns:
        TokenPayload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None


def verify_token_type(token: str, expected_type: str) -> Optional[TokenPayload]:
    """
    Verify that a token is of the expected type.
    
    Args:
        token: The JWT token string
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        TokenPayload if valid and correct type, None otherwise
    """
    payload = decode_token(token)
    if payload and payload.type == expected_type:
        return payload
    return None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def generate_api_key() -> str:
    """Generate a secure random API key."""
    import secrets
    return secrets.token_urlsafe(32)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    import re
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, ""
