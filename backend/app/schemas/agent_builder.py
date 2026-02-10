"""
WorkSynapse Custom Agent Builder Schemas
=========================================

Pydantic schemas for the Custom Agent Builder API.
Includes validation, creation, update, and response schemas.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
import re
from app.schemas.llm import LLMProviderResponse
from app.schemas.rag import RagDocumentResponse


# =============================================================================
# ENUMS (mirroring model enums)
# =============================================================================



class CustomAgentStatusEnum(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    ERROR = "error"


class AgentAutonomyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AgentToolTypeEnum(str, Enum):
    GITHUB = "github"
    SLACK = "slack"
    TELEGRAM = "telegram"
    FILESYSTEM = "filesystem"
    WEB = "web"
    EMAIL = "email"
    DATABASE = "database"
    API = "api"
    CUSTOM = "custom"


class AgentConnectionTypeEnum(str, Enum):
    GITHUB = "github"
    SLACK = "slack"
    TELEGRAM = "telegram"
    JIRA = "jira"
    NOTION = "notion"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    OAUTH = "oauth"
    API_KEY = "api_key"


# =============================================================================
# AGENT MODEL SCHEMAS
# =============================================================================

class AgentModelBase(BaseModel):
    """Base schema for AI models."""
    name: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None


class AgentModelCreate(AgentModelBase):
    """Schema for creating an AI model."""
    provider_id: int
    requires_api_key: bool = True
    api_key_prefix: Optional[str] = None
    base_url: Optional[str] = None
    context_window: int = Field(default=4096, ge=1024)
    max_output_tokens: int = Field(default=4096, ge=100)
    supports_vision: bool = False
    supports_tools: bool = True
    supports_streaming: bool = True
    input_price_per_million: float = Field(default=0.0, ge=0)
    output_price_per_million: float = Field(default=0.0, ge=0)


class AgentModelUpdate(BaseModel):
    """Schema for updating an AI model."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_deprecated: Optional[bool] = None
    input_price_per_million: Optional[float] = Field(default=None, ge=0)
    output_price_per_million: Optional[float] = Field(default=None, ge=0)
    context_window: Optional[int] = Field(default=None, ge=1024)
    max_output_tokens: Optional[int] = Field(default=None, ge=100)


class AgentModelResponse(AgentModelBase):
    """Schema for model response."""
    id: int
    provider_id: int
    provider: Optional["LLMProviderResponse"] = None
    requires_api_key: bool
    api_key_prefix: Optional[str] = None
    context_window: int
    max_output_tokens: int
    supports_vision: bool
    supports_tools: bool
    supports_streaming: bool
    input_price_per_million: float
    output_price_per_million: float
    is_active: bool
    is_deprecated: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AgentModelWithKeyStatus(AgentModelResponse):
    """Model with user's API key status."""
    has_api_key: bool = False
    key_count: int = 0


# =============================================================================
# API KEY SCHEMAS
# =============================================================================

class AgentApiKeyBase(BaseModel):
    """Base schema for API key."""
    provider_id: int
    label: str = Field(default="default", max_length=100)


class AgentApiKeyCreate(AgentApiKeyBase):
    """Schema for creating an API key."""
    api_key: str = Field(..., min_length=10)
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('API key cannot be empty')
        return v.strip()


class AgentApiKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    label: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None


class AgentApiKeyResponse(AgentApiKeyBase):
    """Schema for API key response (no sensitive data)."""
    id: int
    key_preview: str
    is_active: bool
    is_valid: bool
    last_validated_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int
    created_at: datetime
    provider_name: Optional[str] = None

    class Config:
        from_attributes = True


class ApiKeyValidationRequest(BaseModel):
    """Schema for validating an API key."""
    provider_id: int
    api_key: str
    model_name: Optional[str] = None


class ApiKeyValidationResponse(BaseModel):
    """Schema for API key validation response."""
    is_valid: bool
    message: str
    provider: str
    model_tested: Optional[str] = None


# =============================================================================
# AGENT TOOL SCHEMAS
# =============================================================================

class AgentToolConfigBase(BaseModel):
    """Base schema for agent tool."""
    tool_type: AgentToolTypeEnum
    tool_name: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None


class AgentToolConfigCreate(AgentToolConfigBase):
    """Schema for adding a tool to an agent."""
    config_json: Optional[Dict[str, Any]] = None
    is_enabled: bool = True


class AgentToolConfigUpdate(BaseModel):
    """Schema for updating a tool configuration."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class AgentToolConfigResponse(AgentToolConfigBase):
    """Schema for tool response."""
    id: int
    agent_id: int
    config_json: Optional[Dict[str, Any]] = None
    is_enabled: bool
    requires_auth: bool
    is_configured: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# AGENT CONNECTION SCHEMAS
# =============================================================================

class AgentConnectionBase(BaseModel):
    """Base schema for connection."""
    connection_type: AgentConnectionTypeEnum
    name: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None


class AgentConnectionCreate(AgentConnectionBase):
    """Schema for creating a connection."""
    config_json: Optional[Dict[str, Any]] = None


class AgentConnectionUpdate(BaseModel):
    """Schema for updating a connection."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentConnectionResponse(AgentConnectionBase):
    """Schema for connection response."""
    id: int
    agent_id: int
    config_json: Optional[Dict[str, Any]] = None
    is_active: bool
    is_connected: bool
    last_connected_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# MCP SERVER SCHEMAS
# =============================================================================

class AgentMCPServerBase(BaseModel):
    """Base schema for MCP server."""
    server_name: str = Field(..., min_length=2, max_length=100)
    server_url: str = Field(..., min_length=5, max_length=500)
    description: Optional[str] = None


class AgentMCPServerCreate(AgentMCPServerBase):
    """Schema for adding an MCP server."""
    config_json: Optional[Dict[str, Any]] = None
    transport_type: str = "stdio"
    requires_auth: bool = False
    auth_type: Optional[str] = None
    auth_credentials: Optional[str] = None  # Will be encrypted
    
    @field_validator('server_url')
    @classmethod
    def validate_server_url(cls, v: str) -> str:
        # Basic URL/path validation
        if not v.strip():
            raise ValueError('Server URL cannot be empty')
        return v.strip()


class AgentMCPServerUpdate(BaseModel):
    """Schema for updating an MCP server."""
    server_url: Optional[str] = None
    description: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None
    transport_type: Optional[str] = None
    is_enabled: Optional[bool] = None


class AgentMCPServerResponse(AgentMCPServerBase):
    """Schema for MCP server response."""
    id: int
    agent_id: int
    config_json: Optional[Dict[str, Any]] = None
    transport_type: str
    requires_auth: bool
    is_enabled: bool
    is_connected: bool
    last_health_check: Optional[datetime] = None
    last_error: Optional[str] = None
    available_tools: Optional[List[str]] = None
    available_resources: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# CUSTOM AGENT SCHEMAS
# =============================================================================

class CustomAgentBase(BaseModel):
    """Base schema for custom agent."""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class CustomAgentCreate(CustomAgentBase):
    """Schema for creating a custom agent."""
    # Model configuration
    model_id: Optional[int] = None
    local_model_id: Optional[int] = None
    api_key_id: Optional[int] = None
    
    # Model parameters
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=100, le=128000)
    top_p: float = Field(default=1.0, ge=0, le=1)
    frequency_penalty: float = Field(default=0.0, ge=-2, le=2)
    presence_penalty: float = Field(default=0.0, ge=-2, le=2)
    
    # Prompts
    system_prompt: str = Field(..., min_length=10)
    goal_prompt: Optional[str] = None
    service_prompt: Optional[str] = None
    
    # Access
    is_public: bool = False
    
    # Appearance
    avatar_url: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    
    # Memory & RAG
    memory_enabled: bool = False
    memory_config: Optional[Dict[str, Any]] = None
    rag_enabled: bool = False
    rag_config: Optional[Dict[str, Any]] = None
    knowledge_source_ids: Optional[List[int]] = None
    
    # Action Mode
    action_mode_enabled: bool = False
    autonomy_level: AgentAutonomyLevel = AgentAutonomyLevel.LOW
    max_steps: int = Field(default=10, ge=1, le=100)
    mcp_enabled: bool = False

    # Optional nested configurations (for creation in one call)
    tools: Optional[List[AgentToolConfigCreate]] = None
    connections: Optional[List[AgentConnectionCreate]] = None
    mcp_servers: Optional[List[AgentMCPServerCreate]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r'^[\w\s\-]+$', v):
            raise ValueError('Name can only contain letters, numbers, spaces, dashes, and underscores')
        return v.strip()
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
                raise ValueError('Color must be a valid hex color (e.g., #FF5733)')
        return v
    
    @model_validator(mode='after')
    def validate_model_selection(self) -> 'CustomAgentCreate':
        if not self.model_id and not self.local_model_id:
            raise ValueError('Either model_id or local_model_id must be provided')
        if self.model_id and self.local_model_id:
            raise ValueError('Cannot specify both model_id and local_model_id')
        return self


class CustomAgentUpdate(BaseModel):
    """Schema for updating a custom agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    model_id: Optional[int] = None
    local_model_id: Optional[int] = None
    api_key_id: Optional[int] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=100, le=128000)
    top_p: Optional[float] = Field(default=None, ge=0, le=1)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2, le=2)
    presence_penalty: Optional[float] = Field(default=None, ge=-2, le=2)
    system_prompt: Optional[str] = None
    goal_prompt: Optional[str] = None
    service_prompt: Optional[str] = None
    status: Optional[CustomAgentStatusEnum] = None
    is_public: Optional[bool] = None
    avatar_url: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    action_mode_enabled: Optional[bool] = None
    autonomy_level: Optional[AgentAutonomyLevel] = None
    max_steps: Optional[int] = Field(default=None, ge=1, le=100)
    mcp_enabled: Optional[bool] = None


class CustomAgentResponse(CustomAgentBase):
    """Schema for agent response."""
    id: int
    slug: str
    model_id: Optional[int] = None
    local_model_id: Optional[int] = None
    model_name: Optional[str] = None
    model_provider: Optional[str] = None
    api_key_id: Optional[int] = None
    api_key_preview: Optional[str] = None
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    system_prompt: str
    goal_prompt: Optional[str] = None
    service_prompt: Optional[str] = None
    status: CustomAgentStatusEnum
    is_public: bool
    
    # Memory & RAG
    memory_enabled: bool
    memory_config: Optional[Dict[str, Any]] = None
    rag_enabled: bool
    rag_config: Optional[Dict[str, Any]] = None
    
    # Action Mode
    action_mode_enabled: bool
    autonomy_level: AgentAutonomyLevel
    max_steps: int
    mcp_enabled: bool
    
    total_sessions: int
    total_messages: int
    total_tokens_used: int
    total_cost_usd: float
    last_used_at: Optional[datetime] = None
    version: int
    avatar_url: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomAgentDetailResponse(CustomAgentResponse):
    """Detailed agent response with nested data."""
    tools: List[AgentToolConfigResponse] = []
    connections: List[AgentConnectionResponse] = []
    mcp_servers: List[AgentMCPServerResponse] = []
    rag_documents: List[RagDocumentResponse] = []
    # Deprecated
    knowledge_sources: List[Dict[str, Any]] = []


class CustomAgentListResponse(BaseModel):
    """Paginated list of agents."""
    agents: List[CustomAgentResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# =============================================================================
# VALIDATION SCHEMAS
# =============================================================================

class AgentCreationCheck(BaseModel):
    """Check if agent can be created."""
    model_id: int


class AgentCreationCheckResponse(BaseModel):
    """Response for agent creation check."""
    can_create: bool
    has_api_key: bool
    model_name: str
    model_provider: str
    requires_api_key: bool
    available_keys: List[AgentApiKeyResponse] = []
    message: str


class ValidateAgentRequest(BaseModel):
    """Validate full agent configuration."""
    name: str
    model_id: int
    system_prompt: str
    tools: Optional[List[str]] = None


class ValidateAgentResponse(BaseModel):
    """Response for agent validation."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []


# =============================================================================
# EXECUTION SCHEMAS
# =============================================================================

class AgentExecutionRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    thread_id: Optional[uuid.UUID] = None
    stream: bool = False
    metadata: Optional[Dict[str, Any]] = None

class AgentExecutionResponse(BaseModel):
    response: str
    thread_id: Optional[uuid.UUID] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    duration_ms: int = 0


# =============================================================================
# AVAILABLE TOOLS/CONNECTIONS
# =============================================================================

class AvailableToolInfo(BaseModel):
    """Information about an available tool."""
    type: AgentToolTypeEnum
    name: str
    display_name: str
    description: str
    icon: str
    requires_auth: bool
    config_schema: Optional[Dict[str, Any]] = None


class AvailableConnectionInfo(BaseModel):
    """Information about an available connection."""
    type: AgentConnectionTypeEnum
    name: str
    display_name: str
    description: str
    icon: str
    auth_type: str  # oauth, api_key, etc.
    oauth_url: Optional[str] = None
