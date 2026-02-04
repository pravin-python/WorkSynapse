"""
WorkSynapse Schemas Package
===========================
Pydantic schemas for API request/response validation.
"""

from app.schemas.validation import (
    # User
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    # Project
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    # Task
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    # Message
    MessageCreate,
    MessageResponse,
    # Agent
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentMessageInput,
    AgentSessionResponse,
    # Work Log
    WorkLogCreate,
    WorkLogResponse,
    # Common
    PaginationParams,
    PaginatedResponse,
    ErrorResponse,
    ValidationErrorDetail,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    # Task
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    # Message
    "MessageCreate",
    "MessageResponse",
    # Agent
    "AgentCreate",
    "AgentUpdate",
    "AgentResponse",
    "AgentMessageInput",
    "AgentSessionResponse",
    # Work Log
    "WorkLogCreate",
    "WorkLogResponse",
    # Common
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "ValidationErrorDetail",
]
