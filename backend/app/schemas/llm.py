"""
LLM Key Management Schemas
==========================

Pydantic schemas for LLM providers, API keys, and AI agents.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re


# ============================================
# LLM Provider Schemas
# ============================================

class LLMProviderBase(BaseModel):
    """Base schema for LLM Provider."""
    name: str = Field(..., min_length=2, max_length=50)
    display_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    base_url: Optional[str] = None
    requires_api_key: bool = True
    icon: Optional[str] = None


class LLMProviderCreate(LLMProviderBase):
    """Schema for creating a provider."""
    type: str = "custom"
    config_schema: Optional[Dict[str, Any]] = None


class LLMProviderUpdate(BaseModel):
    """Schema for updating a provider."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None
    config_schema: Optional[Dict[str, Any]] = None


class LLMProviderResponse(LLMProviderBase):
    """Schema for provider response."""
    id: int
    type: str
    is_active: bool
    config_schema: Optional[Dict[str, Any]] = None
    config_schema: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LLMProviderWithKeyStatus(LLMProviderResponse):
    """Provider with user's key status."""
    has_api_key: bool = False
    key_count: int = 0


# ============================================
# LLM API Key Schemas
# ============================================

class LLMApiKeyBase(BaseModel):
    """Base schema for API key."""
    label: str = Field(default="default", max_length=100)


class LLMApiKeyCreate(LLMApiKeyBase):
    """Schema for creating an API key."""
    provider_id: int
    api_key: str = Field(..., min_length=10)
    extra_params: Optional[Dict[str, Any]] = None
    
    @field_validator('api_key')
    @classmethod
    def validate_key_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('API key cannot be empty')
        # Basic sanitization - remove whitespace
        return v.strip()


class LLMApiKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    label: Optional[str] = None
    api_key: Optional[str] = None  # If provided, will be re-encrypted
    extra_params: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class LLMApiKeyResponse(LLMApiKeyBase):
    """Schema for API key response (no sensitive data)."""
    id: int
    provider_id: int
    provider_name: Optional[str] = None
    key_preview: str  # Masked key like "sk-ab...xyz"
    extra_params: Optional[Dict[str, Any]] = None
    is_active: bool
    is_valid: bool
    last_used_at: Optional[datetime] = None
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class LLMApiKeyValidation(BaseModel):
    """Schema for key validation request."""
    provider_id: int
    api_key: str


class LLMApiKeyValidationResponse(BaseModel):
    """Schema for key validation response."""
    is_valid: bool
    message: str
    provider: str
    model_tested: Optional[str] = None


# ============================================
# AI Agent Schemas
# ============================================

class AIAgentBase(BaseModel):
    """Base schema for AI Agent."""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    model_name: str = Field(..., min_length=2, max_length=100)


class AIAgentCreate(AIAgentBase):
    """Schema for creating an agent."""
    provider_id: int
    api_key_id: int
    type: str = "assistant"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=100, le=128000)
    system_prompt: Optional[str] = None
    is_public: bool = False
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        # Allow alphanumeric, spaces, dashes, underscores
        if not re.match(r'^[\w\s\-]+$', v):
            raise ValueError('Name can only contain letters, numbers, spaces, dashes, and underscores')
        return v.strip()


class AIAgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    model_name: Optional[str] = None
    api_key_id: Optional[int] = None
    type: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=100, le=128000)
    system_prompt: Optional[str] = None
    status: Optional[str] = None
    is_public: Optional[bool] = None


class AIAgentResponse(AIAgentBase):
    """Schema for agent response."""
    id: int
    provider_id: int
    provider_name: Optional[str] = None
    api_key_id: int
    key_preview: Optional[str] = None
    type: str
    temperature: float
    max_tokens: int
    system_prompt: Optional[str] = None
    status: str
    is_public: bool
    total_requests: int
    total_tokens_used: int
    last_used_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AIAgentCreateCheck(BaseModel):
    """Schema to check if agent can be created."""
    provider_id: int
    model_name: str


class AIAgentCreateCheckResponse(BaseModel):
    """Response for agent creation check."""
    can_create: bool
    has_api_key: bool
    provider_name: str
    available_keys: List[LLMApiKeyResponse] = []
    message: str


# ============================================
# Agent Session Schemas
# ============================================

class AgentSessionResponse(BaseModel):
    """Schema for agent session response."""
    id: int
    agent_id: int
    agent_name: Optional[str] = None
    title: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    message_count: int
    tokens_used: int
    
    class Config:
        from_attributes = True


# ============================================
# Dashboard/Stats Schemas
# ============================================

class LLMKeyStats(BaseModel):
    """Statistics for LLM keys."""
    total_keys: int
    active_keys: int
    providers_with_keys: int
    total_providers: int


class AgentStats(BaseModel):
    """Statistics for agents."""
    total_agents: int
    active_agents: int
    total_requests: int
    total_tokens: int
    agents_by_type: dict
