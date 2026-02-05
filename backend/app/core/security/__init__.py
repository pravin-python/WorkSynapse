"""
WorkSynapse Security Module
===========================
Consolidated security layer providing:
- JWT token management
- Password hashing 
- Authentication utilities
- RBAC decorators
- Security middleware
- Anti-replay protection
- Input sanitization
- Audit logging
- Rate limiting

This is the single source of truth for all security functionality.
"""

# =============================================================================
# AUTHENTICATION & PASSWORD HASHING
# =============================================================================

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
    generate_api_key,
    validate_password_strength,
)

# =============================================================================
# SECURITY DEPENDENCIES
# =============================================================================

from app.core.security.deps import (
    TokenData,
    bearer_scheme,
    get_current_user,
    get_current_user_optional,
    get_current_active_superuser,
    get_client_ip,
    get_user_agent,
    create_access_token as create_user_access_token,
    decode_token as decode_user_token,
)

# =============================================================================
# RBAC (ROLE-BASED ACCESS CONTROL)
# =============================================================================

from app.core.security.rbac import (
    require_permission,
    require_roles,
    RBACChecker,
    check_permission,
    check_any_role,
    check_all_roles,
)

# =============================================================================
# INPUT SANITIZATION
# =============================================================================

from app.core.security.sanitization import (
    InputSanitizer,
    SQLInjectionProtection,
    XSSProtection,
)

# =============================================================================
# AUDIT LOGGING
# =============================================================================

from app.core.security.audit import (
    AuditLogger,
)

# =============================================================================
# RATE LIMITING
# =============================================================================

from app.core.security.rate_limit import (
    generate_rate_limit_key,
    RateLimiter,
    RateLimitPresets,
)

# =============================================================================
# MIDDLEWARE
# =============================================================================

# Note: SecurityMiddleware class not implemented yet - using setup function instead
# Import what exists from middleware.py
from app.core.security.middleware import (
    InputSanitizer as MiddlewareInputSanitizer,
    require_permission as middleware_require_permission,
    require_roles as middleware_require_roles,
    RBACChecker as MiddlewareRBACChecker,
)

from app.core.security.antireplay import (
    AntiReplayMiddleware,
    NonceService,
    setup_antireplay_middleware,
)

# =============================================================================
# MIDDLEWARE SETUP
# =============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def setup_security_middleware(app: FastAPI) -> None:
    """
    Setup security-related middleware for the FastAPI application.
    
    This function configures:
    - CORS middleware
    - Trusted host middleware (production)
    - GZip compression
    """
    # CORS Middleware
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Trusted Host Middleware
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS or ["*"]
        )
    
    # GZip Middleware (compression)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    logger.info("Security middleware configured")


# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Auth utilities
    "TokenPayload",
    "TokenPair",
    "TokenData",
    "pwd_context",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "decode_token",
    "verify_token_type",
    "generate_api_key",
    "validate_password_strength",
    "create_user_access_token",
    "decode_user_token",
    
    # Authentication dependencies
    "bearer_scheme",
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_superuser",
    "get_client_ip",
    "get_user_agent",
    
    # RBAC
    "require_permission",
    "require_roles",
    "RBACChecker",
    "check_permission",
    "check_any_role",
    "check_all_roles",
    
    # Sanitization
    "InputSanitizer",
    "SQLInjectionProtection",
    "XSSProtection",
    
    # Audit
    "AuditLogger",
    
    # Rate limiting
    "generate_rate_limit_key",
    "RateLimiter",
    "RateLimitPresets",
    
    # Middleware
    "AntiReplayMiddleware",
    "NonceService",
    "setup_security_middleware",
    "setup_antireplay_middleware",
]
