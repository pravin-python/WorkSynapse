"""
WorkSynapse Custom Agent Builder Models
========================================

Database models for the Custom Agent Builder feature.
Extends the base agent system with tools, connections, and MCP integrations.

Key Tables:
- custom_agents: Custom agent configurations
- agent_models: Available AI models with provider info
- agent_api_keys: Encrypted API keys per provider
- agent_tools_config: Tool configurations for agents
- agent_connections: External service connections (GitHub, Slack, etc.)
- agent_mcp_servers: MCP server integrations
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.local_models.model import LocalModel
    from app.models.llm.model import LLMKeyProvider
    from app.models.rag import AgentRagDocument
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float,
    ForeignKey, Boolean, Enum as SQLEnum, UniqueConstraint, Index, JSON, Table
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import Base, AuditMixin


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================




# =============================================================================
# ENUMS
# =============================================================================

# NOTE: Provider is now relational (LLMKeyProvider). We no longer use an
# enum type here. Provider-specific metadata and type live in
# `app.models.llm.model.LLMKeyProvider`.


class CustomAgentStatus(str, Enum):
    """Custom agent lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    ERROR = "error"


class AgentAutonomyLevel(str, Enum):
    """Level of agent autonomy."""
    LOW = "low"        # Tool use requires approval
    MEDIUM = "medium"  # Can use safe tools autonomously
    HIGH = "high"      # Fully autonomous execution


class AgentToolType(str, Enum):
    """Types of agent tools."""
    GITHUB = "github"
    SLACK = "slack"
    TELEGRAM = "telegram"
    FILESYSTEM = "filesystem"
    WEB = "web"
    EMAIL = "email"
    DATABASE = "database"
    API = "api"
    CUSTOM = "custom"


class AgentConnectionType(str, Enum):
    """Types of external connections."""
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
# AGENT MODEL DEFINITIONS
# =============================================================================

class AgentModel(Base, AuditMixin):
    """
    Available AI models for agent creation.
    
    Stores metadata about each model including pricing and capabilities.
    """
    __tablename__ = "agent_models"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    provider_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("llm_key_providers.id"),
        nullable=False,
        index=True
    )
    
    provider: Mapped["LLMKeyProvider"] = relationship("LLMKeyProvider", back_populates="models")
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # API requirements
    requires_api_key: Mapped[bool] = mapped_column(Boolean, default=True)
    api_key_prefix: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., "sk-"
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Model specifications
    context_window: Mapped[int] = mapped_column(Integer, default=4096)
    max_output_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_tools: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Pricing (per 1M tokens)
    input_price_per_million: Mapped[float] = mapped_column(Float, default=0.0)
    output_price_per_million: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    custom_agents: Mapped[List["CustomAgent"]] = relationship(
        "CustomAgent",
        back_populates="model"
    )
    
    def __repr__(self):
        provider_name = self.provider.display_name if getattr(self, "provider", None) else "unknown"
        return f"<AgentModel {self.name} ({provider_name})>"


class AgentApiKey(Base, AuditMixin):
    """
    Encrypted API keys for AI providers.
    
    Stores encrypted API keys per user per provider.
    """
    __tablename__ = "agent_api_keys"
    __table_args__ = (
        UniqueConstraint('user_id', 'provider_id', 'label', name='uq_agent_api_key'),
        Index('ix_agent_api_keys_user_provider', 'user_id', 'provider_id'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    provider_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("llm_key_providers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    provider: Mapped["LLMKeyProvider"] = relationship("LLMKeyProvider")
    
    # Key details
    label: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    key_preview: Mapped[str] = mapped_column(String(20), nullable=False)  # Masked preview
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    custom_agents: Mapped[List["CustomAgent"]] = relationship(
        "CustomAgent",
        back_populates="api_key"
    )
    
    def __repr__(self):
        provider_name = self.provider.display_name if getattr(self, "provider", None) else "unknown"
        return f"<AgentApiKey {provider_name} - {self.key_preview}>"


# =============================================================================
# CUSTOM AGENT MODEL
# =============================================================================

class CustomAgent(Base, AuditMixin):
    """
    Custom AI Agent configuration.
    
    The main agent entity created through the Agent Builder.
    Includes model selection, prompts, tools, and connections.
    """
    __tablename__ = "custom_agents"
    __table_args__ = (
        UniqueConstraint('name', 'created_by_user_id', name='uq_custom_agent_name_user'),
        # Index('ix_custom_agents_status', 'status'),  # Defined in mapped_column
        # Index('ix_custom_agents_creator', 'created_by_user_id'),  # Defined in AuditMixin
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Basic Info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Model Configuration
    model_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("agent_models.id", ondelete="RESTRICT"),
        nullable=True
    )
    local_model_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("local_models.id", ondelete="SET NULL"),
        nullable=True
    )
    api_key_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("agent_api_keys.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Model Parameters
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    top_p: Mapped[float] = mapped_column(Float, default=1.0)
    frequency_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    presence_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Prompts
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    goal_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    service_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Memory Configuration
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    memory_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # RAG Configuration
    rag_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    rag_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Memory Configuration
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    memory_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # RAG Configuration
    rag_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    rag_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Action Mode / Autonomy
    action_mode_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    autonomy_level: Mapped[AgentAutonomyLevel] = mapped_column(
        SQLEnum(AgentAutonomyLevel, values_callable=lambda obj: [e.value for e in obj]),
        default=AgentAutonomyLevel.LOW
    )
    max_steps: Mapped[int] = mapped_column(Integer, default=10)
    mcp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    status: Mapped[CustomAgentStatus] = mapped_column(
        SQLEnum(CustomAgentStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=CustomAgentStatus.DRAFT,
        index=True
    )
    
    # Access Control
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Statistics
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Version tracking
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Appearance
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    model: Mapped[Optional["AgentModel"]] = relationship("AgentModel", back_populates="custom_agents")
    local_model: Mapped[Optional["LocalModel"]] = relationship("LocalModel")
    api_key: Mapped[Optional["AgentApiKey"]] = relationship("AgentApiKey", back_populates="custom_agents")
    tools: Mapped[List["AgentToolConfig"]] = relationship(
        "AgentToolConfig",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    connections: Mapped[List["AgentConnection"]] = relationship(
        "AgentConnection",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    mcp_servers: Mapped[List["AgentMCPServer"]] = relationship(
        "AgentMCPServer",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    rag_documents: Mapped[List["AgentRagDocument"]] = relationship(
        "AgentRagDocument",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    prompt_template: Mapped[Optional["AgentPromptTemplate"]] = relationship(
        "AgentPromptTemplate",
        back_populates="agent",
        uselist=False,
        cascade="all, delete-orphan"
    )
    actions: Mapped[List["CustomAgentAction"]] = relationship(
        "CustomAgentAction",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<CustomAgent {self.name} ({self.status.value})>"


# =============================================================================
# AGENT TOOLS CONFIGURATION
# =============================================================================

class AgentToolConfig(Base):
    """
    Tool configuration for a custom agent.
    
    Each agent can have multiple tools with their own configurations.
    """
    __tablename__ = "agent_tools_config"
    __table_args__ = (
        UniqueConstraint('agent_id', 'tool_type', name='uq_agent_tool'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Tool info
    tool_type: Mapped[AgentToolType] = mapped_column(
        SQLEnum(AgentToolType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuration (JSON blob)
    config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_auth: Mapped[bool] = mapped_column(Boolean, default=False)
    is_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    agent: Mapped["CustomAgent"] = relationship("CustomAgent", back_populates="tools")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AgentToolConfig {self.tool_name} for Agent {self.agent_id}>"


# =============================================================================
# AGENT CONNECTIONS
# =============================================================================

class AgentConnection(Base, AuditMixin):
    """
    External service connections for agents.
    
    Stores OAuth tokens, API keys, and webhook configurations.
    """
    __tablename__ = "agent_connections"
    __table_args__ = (
        UniqueConstraint('agent_id', 'connection_type', 'name', name='uq_agent_connection'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Connection info
    connection_type: Mapped[AgentConnectionType] = mapped_column(
        SQLEnum(AgentConnectionType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuration (encrypted if sensitive)
    config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    encrypted_credentials: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # OAuth fields
    oauth_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    oauth_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    oauth_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    oauth_scope: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    agent: Mapped["CustomAgent"] = relationship("CustomAgent", back_populates="connections")
    
    def __repr__(self):
        return f"<AgentConnection {self.connection_type.value} for Agent {self.agent_id}>"


# =============================================================================
# AGENT MCP SERVERS
# =============================================================================

class AgentMCPServer(Base):
    """
    MCP (Model Context Protocol) server integration.
    
    Allows agents to connect to MCP servers for extended capabilities.
    """
    __tablename__ = "agent_mcp_servers"
    __table_args__ = (
        UniqueConstraint('agent_id', 'server_name', name='uq_agent_mcp_server'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Server info
    server_name: Mapped[str] = mapped_column(String(100), nullable=False)
    server_url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Configuration
    config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    transport_type: Mapped[str] = mapped_column(String(50), default="stdio")  # stdio, sse, websocket
    
    # Authentication
    requires_auth: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # bearer, api_key, none
    encrypted_auth: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    last_health_check: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Available tools/resources from this server
    available_tools: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    available_resources: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    agent: Mapped["CustomAgent"] = relationship("CustomAgent", back_populates="mcp_servers")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AgentMCPServer {self.server_name} for Agent {self.agent_id}>"


# =============================================================================
# AGENT PROMPTS
# =============================================================================

class AgentPromptTemplate(Base, AuditMixin):
    """
    Structured prompt templates for LangChain-style architecture.
    """
    __tablename__ = "agent_prompt_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        nullable=False
    )

    # Prompt Components
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    goal_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instruction_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    agent: Mapped["CustomAgent"] = relationship("CustomAgent", back_populates="prompt_template")


class AgentRuntimePromptData(Base, AuditMixin):
    """
    Runtime dynamic prompt data for specific sessions.
    """
    __tablename__ = "agent_runtime_prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        nullable=False
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Dynamic Components
    user_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    memory_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scratchpad_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    agent: Mapped["CustomAgent"] = relationship("CustomAgent")


class CustomAgentAction(Base, AuditMixin):
    """
    Defines allowed actions or workflows for a custom agent.
    """
    __tablename__ = "custom_agent_actions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        nullable=False
    )
    action_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(50), default="manual")  # manual, auto, event
    config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    agent: Mapped["CustomAgent"] = relationship("CustomAgent", back_populates="actions")

