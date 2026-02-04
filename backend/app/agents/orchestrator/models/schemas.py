"""
Pydantic Schemas for Agent Orchestrator
=======================================

Request/response schemas for the agent API.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from enum import Enum


class LLMProviderEnum(str, Enum):
    """Supported LLM providers."""

    openai = "openai"
    ollama = "ollama"
    gemini = "gemini"
    claude = "claude"
    huggingface = "huggingface"


class MemoryTypeEnum(str, Enum):
    """Supported memory types."""

    conversation = "conversation"
    vector = "vector"
    session = "session"
    none = "none"


class ToolConfig(BaseModel):
    """Configuration for a single tool."""

    name: str = Field(..., description="Tool identifier")
    enabled: bool = Field(default=True, description="Whether tool is active")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Tool-specific configuration"
    )


class ChatMessage(BaseModel):
    """A single chat message."""

    role: Literal["user", "assistant", "system", "tool"] = Field(
        ..., description="Message role"
    )
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(default=None, description="Name for tool messages")
    tool_call_id: Optional[str] = Field(
        default=None, description="ID of associated tool call"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class PermissionConfig(BaseModel):
    """Permission configuration for an agent."""

    can_access_internet: bool = Field(default=True)
    can_access_files: bool = Field(default=False)
    can_execute_code: bool = Field(default=False)
    can_send_emails: bool = Field(default=False)
    can_modify_data: bool = Field(default=False)
    can_access_github: bool = Field(default=True)
    can_send_messages: bool = Field(default=True)
    allowed_tools: List[str] = Field(default_factory=list)
    denied_tools: List[str] = Field(default_factory=list)


class AdvancedConfig(BaseModel):
    """Advanced agent configuration."""

    enable_planning: bool = Field(default=True)
    enable_reasoning: bool = Field(default=True)
    can_stop_itself: bool = Field(default=False)
    max_iterations: int = Field(default=10, ge=1, le=50)
    timeout_seconds: int = Field(default=300, ge=30, le=1800)
    retry_on_failure: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=0, le=10)


# ========================
# AGENT SCHEMAS
# ========================


class AgentCreate(BaseModel):
    """Schema for creating a new agent."""

    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    system_prompt: str = Field(
        ...,
        min_length=10,
        description="Core system prompt defining agent behavior",
    )
    goal: Optional[str] = Field(None, description="Agent's primary objective")
    identity_guidance: Optional[str] = Field(
        None, description="Additional identity context"
    )

    # LLM Configuration
    llm_provider: LLMProviderEnum = Field(
        default=LLMProviderEnum.openai, description="LLM provider to use"
    )
    model_name: str = Field(default="gpt-4o", description="Model identifier")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int = Field(default=4096, ge=100, le=128000, description="Max tokens")

    # Tools
    tools: List[ToolConfig] = Field(
        default_factory=list, description="Assigned tools"
    )

    # Memory
    memory_type: MemoryTypeEnum = Field(
        default=MemoryTypeEnum.conversation, description="Memory system type"
    )
    enable_long_term_memory: bool = Field(
        default=False, description="Enable vector memory"
    )
    memory_config: Dict[str, Any] = Field(
        default_factory=dict, description="Memory configuration"
    )

    # Permissions
    permissions: PermissionConfig = Field(
        default_factory=PermissionConfig, description="Permission settings"
    )

    # Advanced
    config: AdvancedConfig = Field(
        default_factory=AdvancedConfig, description="Advanced configuration"
    )

    # Visibility
    is_public: bool = Field(default=False, description="Whether agent is public")

    @field_validator("system_prompt")
    @classmethod
    def validate_system_prompt(cls, v: str) -> str:
        """Ensure system prompt is not empty and reasonably formatted."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("System prompt must be at least 10 characters")
        return v


class AgentUpdate(BaseModel):
    """Schema for updating an existing agent."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = Field(None, min_length=10)
    goal: Optional[str] = None
    identity_guidance: Optional[str] = None

    llm_provider: Optional[LLMProviderEnum] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=100, le=128000)

    tools: Optional[List[ToolConfig]] = None
    memory_type: Optional[MemoryTypeEnum] = None
    enable_long_term_memory: Optional[bool] = None
    memory_config: Optional[Dict[str, Any]] = None

    permissions: Optional[PermissionConfig] = None
    config: Optional[AdvancedConfig] = None

    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class AgentResponse(BaseModel):
    """Schema for agent response."""

    id: int
    name: str
    description: Optional[str]
    system_prompt: str
    goal: Optional[str]
    identity_guidance: Optional[str]

    llm_provider: str
    model_name: str
    temperature: float
    max_tokens: int

    tools: List[Dict[str, Any]]
    memory_type: str
    enable_long_term_memory: bool
    memory_config: Dict[str, Any]

    permissions: Dict[str, Any]
    config: Dict[str, Any]

    is_active: bool
    is_public: bool
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Schema for paginated agent list."""

    agents: List[AgentResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ========================
# CONVERSATION SCHEMAS
# ========================


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    agent_id: int = Field(..., description="ID of the agent")
    title: Optional[str] = Field(None, max_length=255, description="Conversation title")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: int
    agent_id: int
    user_id: Optional[UUID]
    thread_id: UUID
    title: Optional[str]
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list."""

    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int


# ========================
# EXECUTION SCHEMAS
# ========================


class ExecutionRequest(BaseModel):
    """Schema for requesting agent execution."""

    message: str = Field(..., min_length=1, description="User message to process")
    conversation_id: Optional[int] = Field(
        None, description="Existing conversation ID to continue"
    )
    thread_id: Optional[UUID] = Field(
        None, description="LangGraph thread ID for state recovery"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Execution metadata"
    )
    stream: bool = Field(default=False, description="Whether to stream response")


class ToolCallInfo(BaseModel):
    """Information about a tool call made during execution."""

    tool: str
    args: Dict[str, Any]
    result: Optional[str]
    duration_ms: int = 0


class ExecutionResponse(BaseModel):
    """Schema for execution response."""

    id: int
    agent_id: int
    conversation_id: Optional[int]
    thread_id: UUID

    input_message: str
    output_message: Optional[str]

    tool_calls: List[ToolCallInfo]

    tokens_input: int
    tokens_output: int
    tokens_total: int
    duration_ms: int

    status: str
    error: Optional[str]

    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ExecutionStreamChunk(BaseModel):
    """Schema for streaming response chunks."""

    chunk_type: Literal["token", "tool_start", "tool_end", "step", "done", "error"]
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[str] = None
    step_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ========================
# TOOL SCHEMAS
# ========================


class AvailableToolResponse(BaseModel):
    """Schema for available tool information."""

    name: str
    description: str
    category: str
    parameters: Dict[str, Any]
    requires_config: bool = False
    required_permissions: List[str] = Field(default_factory=list)


class ToolListResponse(BaseModel):
    """Schema for list of available tools."""

    tools: List[AvailableToolResponse]
    categories: List[str]


# ========================
# PROVIDER SCHEMAS
# ========================


class ProviderInfo(BaseModel):
    """Schema for LLM provider information."""

    name: str
    display_name: str
    available: bool
    models: List[str]
    default_model: str
    supports_streaming: bool = True
    supports_tools: bool = True


class ProviderListResponse(BaseModel):
    """Schema for list of available providers."""

    providers: List[ProviderInfo]
