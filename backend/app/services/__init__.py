"""
WorkSynapse Services Package
============================
Service layer for business logic and data access.

Services:
- auth_service: Authentication operations
- user_service: User management
- agent_service: Agent management
- project_service: Project operations
- websocket_service: Real-time communication
- redis_service: Redis caching
- kafka_service: Message queue operations
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
from app.services.auth_service import auth_service, AuthService, AuthenticationError
from app.services.project_service import project_service, ProjectService
from app.services.websocket_service import websocket_service, WebSocketService
from app.services.redis_service import redis_service
from app.services.kafka_service import kafka_service

__all__ = [
    # Base
    "SecureCRUDBase",
    "CRUDException",
    "NotFoundError",
    "DuplicateError",
    "ValidationError",
    "PermissionError",
    # Auth
    "auth_service",
    "AuthService",
    "AuthenticationError",
    # User
    "user_service",
    "UserService",
    # Agent
    "agent_service",
    "AgentService",
    # Project
    "project_service",
    "ProjectService",
    # WebSocket
    "websocket_service",
    "WebSocketService",
    # Infrastructure
    "redis_service",
    "kafka_service",
]
