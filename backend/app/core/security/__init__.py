"""
WorkSynapse Security Module
===========================
Consolidated security layer providing:
- JWT token management
- Password hashing 
- Authentication utilities
- Security middleware
- Anti-replay protection

This is the single source of truth for all security functionality.
"""

from app.core.security.auth import (
    TokenPayload,
    TokenPair,
    pwd_context,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    verify_token_type,
)

from app.core.security.middleware import (
    SecurityMiddleware,
)

from app.core.security.antireplay import (
    AntiReplayMiddleware,
    NonceStore,
)

__all__ = [
    # Auth utilities
    "TokenPayload",
    "TokenPair",
    "pwd_context",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "decode_token",
    "verify_token_type",
    # Middleware
    "SecurityMiddleware",
    "AntiReplayMiddleware",
    "NonceStore",
]
