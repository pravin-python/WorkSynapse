"""
LLM Key Management Models
=========================

SQLAlchemy models for LLM API key providers, encrypted keys, and user AI agents.

NOTE: These models are separate from the system-level Agent/AgentSession models
in app.models.agent.model. These are USER-created agents using stored API keys.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, 
    ForeignKey, Boolean, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import Base, AuditMixin


class LLMKeyProviderType(str, Enum):
    """Supported LLM key providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GEMINI = "gemini"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    GROQ = "groq"
    AWS_BEDROCK = "aws_bedrock"
    DEEPSEEK = "deepseek"
    CUSTOM = "custom"


class LLMKeyProvider(Base, AuditMixin):
    """
    LLM Key Provider configuration.
    
    Stores metadata about each LLM provider for API key management.
    This is for managing user API keys, not the system Agent LLMProvider enum.
    """
    __tablename__ = "llm_key_providers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    type: Mapped[LLMKeyProviderType] = mapped_column(
        SQLEnum(LLMKeyProviderType), 
        nullable=False,
        default=LLMKeyProviderType.CUSTOM
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_api_key: Mapped[bool] = mapped_column(Boolean, default=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Icon name
    
    # Configuration schema for extra parameters (JSON)
    config_schema: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # System provider fields
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # If True, cannot be deleted
    purchase_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Link to buy API keys
    documentation_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Link to docs
    
    # Relationships
    models: Mapped[List["AgentModel"]] = relationship(
        "AgentModel",
        back_populates="provider",
        cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["LLMApiKey"]] = relationship(
        "LLMApiKey", 
        back_populates="provider",
        cascade="all, delete-orphan"
    )
    user_agents: Mapped[List["UserAIAgent"]] = relationship(
        "UserAIAgent",
        back_populates="provider"
    )
    
    def __repr__(self):
        return f"<LLMKeyProvider {self.name}>"


class LLMApiKey(Base, AuditMixin):
    """
    Encrypted LLM API Key storage.
    
    Stores encrypted API keys for LLM providers.
    Keys are encrypted using Fernet symmetric encryption.
    """
    __tablename__ = "llm_api_keys"
    __table_args__ = (
        UniqueConstraint('provider_id', 'user_id', 'label', name='uq_llm_key_provider_user_label'),
        Index('ix_llm_api_keys_user_provider', 'user_id', 'provider_id'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("llm_key_providers.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Key details
    label: Mapped[str] = mapped_column(String(100), nullable=False, default="default")
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    key_preview: Mapped[str] = mapped_column(String(20), nullable=False)  # Masked preview
    
    # Extra parameters (JSON) for things like region, endpoint, etc.
    extra_params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)  # Set False if key fails
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Rate limit tracking
    requests_this_month: Mapped[int] = mapped_column(Integer, default=0)
    tokens_this_month: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    provider: Mapped["LLMKeyProvider"] = relationship("LLMKeyProvider", back_populates="api_keys")
    user: Mapped["User"] = relationship("User", back_populates="llm_api_keys", foreign_keys=[user_id])
    user_agents: Mapped[List["UserAIAgent"]] = relationship("UserAIAgent", back_populates="api_key")
    
    def __repr__(self):
        return f"<LLMApiKey {self.key_preview}>"


class UserAgentType(str, Enum):
    """Types of user-created AI agents."""
    PLANNING = "planning"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    ANALYTICS = "analytics"
    ASSISTANT = "assistant"
    CUSTOM = "custom"


class UserAgentStatus(str, Enum):
    """User agent status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class UserAIAgent(Base, AuditMixin):
    """
    User-created AI Agent configuration.
    
    Stores configuration for user-created AI agents using their stored API keys.
    This is separate from system-level Agents in app.models.agent.
    """
    __tablename__ = "user_ai_agents"
    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='uq_user_agent_name_user'),
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
        nullable=False
    )
    api_key_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("llm_api_keys.id", ondelete="RESTRICT"),
        nullable=False
    )
    
    # Agent configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    agent_type: Mapped[UserAgentType] = mapped_column(
        SQLEnum(UserAgentType),
        default=UserAgentType.ASSISTANT
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Agent settings
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[UserAgentStatus] = mapped_column(
        SQLEnum(UserAgentStatus),
        default=UserAgentStatus.ACTIVE
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Usage tracking
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="ai_agents", foreign_keys=[user_id])
    provider: Mapped["LLMKeyProvider"] = relationship("LLMKeyProvider", back_populates="user_agents")
    api_key: Mapped["LLMApiKey"] = relationship("LLMApiKey", back_populates="user_agents")
    sessions: Mapped[List["UserAgentSession"]] = relationship(
        "UserAgentSession",
        back_populates="user_agent",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<UserAIAgent {self.name} ({self.model_name})>"


class UserAgentSession(Base):
    """
    User agent conversation session.
    
    Tracks individual conversation sessions with a user-created agent.
    """
    __tablename__ = "user_agent_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_ai_agents.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Session data
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Metrics
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    user_agent: Mapped["UserAIAgent"] = relationship("UserAIAgent", back_populates="sessions")
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self):
        return f"<UserAgentSession {self.id}>"


# Note: User model relationships are defined via string references above
# The User import is not needed here because SQLAlchemy resolves
# relationship targets by string name at runtime
