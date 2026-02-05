"""
WorkSynapse Middleware Package
==============================
Security and request processing middleware.

This module re-exports security functionality from the consolidated
app.core.security module for backward compatibility.
"""

# Import from consolidated security module
from app.core.security import (
    # Token handling
    TokenData,
    create_access_token,
    decode_token,
    # Authentication dependencies
    get_current_user,
    get_current_user_optional,
    get_current_active_superuser,
    # RBAC decorators
    require_permission,
    require_roles,
    RBACChecker,
    # Input sanitization
    InputSanitizer,
    SQLInjectionProtection,
    # Audit logging
    AuditLogger,
    # Request context
    get_client_ip,
    get_user_agent,
    # Rate limiting
    generate_rate_limit_key,
    # Middleware setup
    setup_security_middleware,
)

__all__ = [
    # Token handling
    "TokenData",
    "create_access_token",
    "decode_token",
    # Authentication
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_superuser",
    # RBAC
    "require_permission",
    "require_roles",
    "RBACChecker",
    # Sanitization
    "InputSanitizer",
    "SQLInjectionProtection",
    # Audit
    "AuditLogger",
    # Context
    "get_client_ip",
    "get_user_agent",
    # Rate limiting
    "generate_rate_limit_key",
    # Middleware setup
    "setup_security_middleware",
]
