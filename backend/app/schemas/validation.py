"""
WorkSynapse Validation Schemas
==============================
Pydantic schemas for API request/response validation.

Features:
- Input validation with custom validators
- Length limits
- Regex validation for emails, URLs
- JSON schema validation for AI inputs
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from datetime import datetime, date
import re


# =============================================================================
# COMMON VALIDATORS
# =============================================================================

def validate_not_empty(v: str, field_name: str) -> str:
    """Ensure string is not empty or whitespace only."""
    if not v or not v.strip():
        raise ValueError(f"{field_name} cannot be empty")
    return v.strip()


def validate_max_length(v: str, max_len: int, field_name: str) -> str:
    """Ensure string doesn't exceed maximum length."""
    if len(v) > max_len:
        raise ValueError(f"{field_name} must be at most {max_len} characters")
    return v


def validate_safe_string(v: str) -> str:
    """Remove potentially dangerous characters."""
    # Remove null bytes
    v = v.replace('\x00', '')
    # Remove control characters except newlines and tabs
    v = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', v)
    return v


# =============================================================================
# USER SCHEMAS
# =============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = validate_safe_string(v)
        return validate_not_empty(v, "Full name")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = validate_safe_string(v)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must be at most 128 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = Field(None, max_length=512)
    timezone: Optional[str] = Field(None, max_length=50)
    locale: Optional[str] = Field(None, max_length=10)


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_superuser: bool
    role: str
    email_verified: bool
    mfa_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# =============================================================================
# PROJECT SCHEMAS
# =============================================================================

class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    key: str = Field(..., min_length=2, max_length=10)
    visibility: str = Field(default="PRIVATE")
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = validate_safe_string(v)
        return validate_not_empty(v, "Project name")
    
    @field_validator('key')
    @classmethod
    def validate_key(cls, v: str) -> str:
        v = validate_safe_string(v)
        if not re.match(r'^[A-Z0-9]+$', v.upper()):
            raise ValueError('Project key must be alphanumeric')
        return v.upper()
    
    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_date and self.target_end_date:
            if self.target_end_date < self.start_date:
                raise ValueError('Target end date must be after start date')
        return self


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[str] = None
    visibility: Optional[str] = None
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: int
    name: str
    description: Optional[str]
    key: str
    status: str
    visibility: str
    owner_id: int
    start_date: Optional[date]
    target_end_date: Optional[date]
    task_counter: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# TASK SCHEMAS
# =============================================================================

class TaskCreate(BaseModel):
    """Schema for creating a task."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=50000)
    project_id: int
    status: str = Field(default="BACKLOG")
    priority: str = Field(default="MEDIUM")
    task_type: str = Field(default="TASK")
    assignee_id: Optional[int] = None
    sprint_id: Optional[int] = None
    milestone_id: Optional[int] = None
    due_date: Optional[date] = None
    start_date: Optional[date] = None
    estimated_minutes: Optional[int] = Field(None, ge=0)
    story_points: Optional[float] = Field(None, ge=0)
    label_ids: Optional[List[int]] = None
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = validate_safe_string(v)
        return validate_not_empty(v, "Task title")
    
    @model_validator(mode='after')
    def validate_dates(self):
        if self.start_date and self.due_date:
            if self.due_date < self.start_date:
                raise ValueError('Due date must be after start date')
        return self


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=50000)
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    sprint_id: Optional[int] = None
    column_id: Optional[int] = None
    due_date: Optional[date] = None
    start_date: Optional[date] = None
    estimated_minutes: Optional[int] = Field(None, ge=0)
    story_points: Optional[float] = Field(None, ge=0)


class TaskResponse(BaseModel):
    """Schema for task response."""
    id: int
    task_number: str
    title: str
    description: Optional[str]
    project_id: int
    status: str
    priority: str
    task_type: str
    assignee_id: Optional[int]
    sprint_id: Optional[int]
    due_date: Optional[date]
    estimated_minutes: Optional[int]
    logged_minutes: int
    story_points: Optional[float]
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# MESSAGE SCHEMAS
# =============================================================================

class MessageCreate(BaseModel):
    """Schema for creating a message."""
    content: str = Field(..., min_length=1, max_length=10000)
    channel_id: int
    content_type: str = Field(default="TEXT")
    parent_message_id: Optional[int] = None
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = validate_safe_string(v)
        return validate_not_empty(v, "Message content")


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: int
    content: str
    content_type: str
    channel_id: int
    sender_id: int
    parent_message_id: Optional[int]
    is_edited: bool
    thread_reply_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# AI AGENT SCHEMAS
# =============================================================================

class AgentCreate(BaseModel):
    """Schema for creating an AI agent."""
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=5000)
    agent_type: str = Field(default="CUSTOM")
    llm_provider: str = Field(default="OPENAI")
    llm_model: str = Field(..., max_length=100)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1, le=128000)
    system_prompt: str = Field(..., min_length=10, max_length=50000)
    goals: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must be lowercase alphanumeric with hyphens only')
        return v
    
    @field_validator('system_prompt')
    @classmethod
    def validate_system_prompt(cls, v: str) -> str:
        v = validate_safe_string(v)
        return validate_not_empty(v, "System prompt")


class AgentUpdate(BaseModel):
    """Schema for updating an AI agent."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[str] = None
    llm_model: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    system_prompt: Optional[str] = Field(None, min_length=10, max_length=50000)
    goals: Optional[List[str]] = None


class AgentMessageInput(BaseModel):
    """Schema for AI agent chat message input."""
    message: str = Field(..., min_length=1, max_length=32000)
    context: Optional[Dict[str, Any]] = None
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = validate_safe_string(v)
        return validate_not_empty(v, "Message")
    
    @field_validator('context')
    @classmethod
    def validate_context(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        # Limit context size
        import json
        context_str = json.dumps(v)
        if len(context_str) > 100000:  # 100KB limit
            raise ValueError('Context too large')
        return v


class AgentResponse(BaseModel):
    """Schema for AI agent response."""
    id: int
    name: str
    slug: str
    description: Optional[str]
    agent_type: str
    status: str
    llm_provider: str
    llm_model: str
    total_sessions: int
    total_messages: int
    total_tokens_used: int
    total_cost_usd: float
    last_used_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentSessionResponse(BaseModel):
    """Schema for agent session response."""
    id: int
    session_uuid: str
    agent_id: int
    user_id: int
    status: str
    title: Optional[str]
    message_count: int
    total_tokens_used: int
    total_cost_usd: float
    started_at: datetime
    ended_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# =============================================================================
# WORK LOG SCHEMAS
# =============================================================================

class WorkLogCreate(BaseModel):
    """Schema for creating a work log."""
    task_id: Optional[int] = None
    project_id: Optional[int] = None
    work_date: date
    duration_seconds: int = Field(..., ge=0, le=86400)  # Max 24 hours
    description: Optional[str] = Field(None, max_length=5000)
    is_billable: bool = True
    
    @model_validator(mode='after')
    def validate_association(self):
        # At least one of task_id or project_id should be set
        if not self.task_id and not self.project_id:
            raise ValueError('Either task_id or project_id must be provided')
        return self


class WorkLogResponse(BaseModel):
    """Schema for work log response."""
    id: int
    user_id: int
    task_id: Optional[int]
    project_id: Optional[int]
    work_date: date
    duration_seconds: int
    description: Optional[str]
    productivity_score: Optional[int]
    is_billable: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# PAGINATION SCHEMAS
# =============================================================================

class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)
    order_by: Optional[str] = None
    order_desc: bool = False


class PaginatedResponse(BaseModel):
    """Schema for paginated response."""
    items: List[Any]
    total: int
    skip: int
    limit: int
    has_more: bool


# =============================================================================
# ERROR SCHEMAS
# =============================================================================

class ErrorResponse(BaseModel):
    """Schema for error response."""
    detail: str
    error_code: Optional[str] = None
    field_errors: Optional[Dict[str, List[str]]] = None


class ValidationErrorDetail(BaseModel):
    """Schema for validation error detail."""
    loc: List[Union[str, int]]
    msg: str
    type: str
