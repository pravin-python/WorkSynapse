"""
WorkSynapse Services Package
============================
Service layer for business logic and data access.
"""

from app.services.base import (
    SecureCRUDBase,
    CRUDException,
    NotFoundError,
    DuplicateError,
    ValidationError,
    PermissionError,
)
from app.services.user import user_service, UserService
from app.services.agent import agent_service, AgentService

__all__ = [
    # Base
    "SecureCRUDBase",
    "CRUDException",
    "NotFoundError",
    "DuplicateError",
    "ValidationError",
    "PermissionError",
    # User
    "user_service",
    "UserService",
    # Agent
    "agent_service",
    "AgentService",
]
