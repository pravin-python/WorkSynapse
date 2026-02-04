"""
WorkSynapse AI Agent Governance Models
======================================
Complete AI agent governance system with full auditability.

CRITICAL SYSTEM FEATURES:
- Agent lifecycle management
- Permission-based access control
- Complete conversation history
- LLM API call logging
- Tool usage tracking
- Token consumption & cost tracking
- Action audit trail
- AI-generated task tracking

Security Requirements:
- Every agent action is logged
- Token usage tracked per call
- Prompt/output stored for audit
- Cost estimation per operation
"""
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, Enum, ForeignKey, Text, Integer, 
    DateTime, Index, UniqueConstraint, CheckConstraint,
    JSON, Table, Column, Float, BigInteger
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin
import enum
import datetime


# =============================================================================
# ENUMS
# =============================================================================

class AgentStatus(str, enum.Enum):
    """Agent lifecycle status."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class AgentType(str, enum.Enum):
    """Pre-defined agent types."""
    CUSTOM = "CUSTOM"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    TASK_GENERATOR = "TASK_GENERATOR"
    CODE_ASSISTANT = "CODE_ASSISTANT"
    PRODUCTIVITY = "PRODUCTIVITY"
    DOCUMENTATION = "DOCUMENTATION"
    TESTING = "TESTING"
    DATA_ANALYST = "DATA_ANALYST"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"


class LLMProvider(str, enum.Enum):
    """Supported LLM providers."""
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    GOOGLE = "GOOGLE"
    AZURE_OPENAI = "AZURE_OPENAI"
    LOCAL = "LOCAL"
    CUSTOM = "CUSTOM"


class LLMModel(str, enum.Enum):
    """Supported LLM models."""
    # OpenAI
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_35_TURBO = "gpt-3.5-turbo"
    # Anthropic
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    CLAUDE_35_SONNET = "claude-3.5-sonnet"
    # Google
    GEMINI_PRO = "gemini-pro"
    GEMINI_ULTRA = "gemini-ultra"
    GEMINI_15_PRO = "gemini-1.5-pro"
    GEMINI_15_FLASH = "gemini-1.5-flash"
    # Custom
    CUSTOM = "custom"


class AgentSessionStatus(str, enum.Enum):
    """Agent session status."""
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    ENDED = "ENDED"
    ERROR = "ERROR"


class AgentCallStatus(str, enum.Enum):
    """LLM API call status."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"


class AgentActionType(str, enum.Enum):
    """Types of agent actions."""
    TOOL_CALL = "TOOL_CALL"
    TASK_CREATE = "TASK_CREATE"
    TASK_UPDATE = "TASK_UPDATE"
    PROJECT_CREATE = "PROJECT_CREATE"
    FILE_CREATE = "FILE_CREATE"
    FILE_UPDATE = "FILE_UPDATE"
    MESSAGE_SEND = "MESSAGE_SEND"
    API_CALL = "API_CALL"
    DATABASE_QUERY = "DATABASE_QUERY"
    EXTERNAL_INTEGRATION = "EXTERNAL_INTEGRATION"


class AgentActionStatus(str, enum.Enum):
    """Status of agent actions."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================

# Many-to-many: Agents <-> Tools
agent_tools = Table(
    "agent_tools_mapping",
    Base.metadata,
    Column("agent_id", Integer, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
    Column("tool_id", Integer, ForeignKey("agent_tools.id", ondelete="CASCADE"), primary_key=True),
    Column("is_enabled", Boolean, default=True),
    Column("added_at", DateTime(timezone=True), server_default="now()"),
)

# Many-to-many: Agents <-> Roles (which roles can use the agent)
agent_role_permissions = Table(
    "agent_role_permissions",
    Base.metadata,
    Column("agent_id", Integer, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("can_execute", Boolean, default=True),
    Column("can_configure", Boolean, default=False),
)


# =============================================================================
# AGENT MODEL
# =============================================================================

class Agent(Base, AuditMixin):
    """
    AI Agent definition and configuration.
    
    Each agent has:
    - Custom system prompt and goals
    - Assigned tools
    - LLM configuration
    - Role-based permissions
    - Usage tracking
    """
    __tablename__ = "agents"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Type and status
    agent_type: Mapped[AgentType] = mapped_column(
        Enum(AgentType),
        default=AgentType.CUSTOM
    )
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus),
        default=AgentStatus.DRAFT,
        index=True
    )
    
    # LLM Configuration
    llm_provider: Mapped[LLMProvider] = mapped_column(
        Enum(LLMProvider),
        default=LLMProvider.OPENAI
    )
    llm_model: Mapped[str] = mapped_column(String(100), nullable=False)  # Using string for flexibility
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    
    # System prompt (core instruction for the agent)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Goals and capabilities
    goals: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of goals
    capabilities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Access control
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)  # All users can access
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # System-managed agent
    
    # Rate limiting
    max_calls_per_minute: Mapped[int] = mapped_column(Integer, default=10)
    max_calls_per_day: Mapped[int] = mapped_column(Integer, default=1000)
    max_tokens_per_call: Mapped[int] = mapped_column(Integer, default=8192)
    
    # Cost control
    max_cost_per_day_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Memory configuration
    memory_type: Mapped[str] = mapped_column(String(50), default="buffer")  # buffer, summary, vector
    memory_window_size: Mapped[int] = mapped_column(Integer, default=10)
    
    # Project scope (optional - agent can be project-specific)
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    
    # Appearance
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # Statistics
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(BigInteger, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Last activity
    last_used_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Version for config changes
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Relationships
    project = relationship("Project")
    tools: Mapped[List["AgentTool"]] = relationship(
        secondary=agent_tools,
        back_populates="agents"
    )
    role_permissions = relationship(
        "Role",
        secondary=agent_role_permissions,
        backref="accessible_agents"
    )
    user_permissions: Mapped[List["AgentUserPermission"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    sessions: Mapped[List["AgentSession"]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint("temperature >= 0 AND temperature <= 2", name="check_temperature_range"),
        CheckConstraint("max_tokens > 0", name="check_max_tokens_positive"),
        CheckConstraint("max_calls_per_minute > 0", name="check_rate_limit_positive"),
        Index("ix_agents_status_type", "status", "agent_type"),
        Index("ix_agents_project", "project_id"),
    )


# =============================================================================
# AGENT USER PERMISSION MODEL
# =============================================================================

class AgentUserPermission(Base):
    """
    Individual user permissions for agents.
    """
    __tablename__ = "agent_user_permissions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Agent reference
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # User reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Permissions
    can_use: Mapped[bool] = mapped_column(Boolean, default=True)
    can_configure: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_logs: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Per-user rate limits (override agent defaults)
    custom_rate_limit_per_minute: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    custom_rate_limit_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Granted by
    granted_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="user_permissions")
    user = relationship("User", foreign_keys=[user_id])
    granted_by = relationship("User", foreign_keys=[granted_by_user_id])
    
    __table_args__ = (
        UniqueConstraint("agent_id", "user_id", name="uq_agent_user_permission"),
    )


# =============================================================================
# AGENT TOOL MODEL
# =============================================================================

class AgentTool(Base):
    """
    Tool/function definitions that agents can use.
    
    Tools are capabilities that agents can invoke to perform actions.
    """
    __tablename__ = "agent_tools"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Identity
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Tool type
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # productivity, code, data, communication
    
    # Function schema (OpenAI function calling format)
    function_schema: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Implementation reference
    handler_module: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., "app.agents.tools.github"
    handler_function: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "create_issue"
    
    # Access control
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)  # Needs human approval
    is_dangerous: Mapped[bool] = mapped_column(Boolean, default=False)  # Can modify/delete data
    
    # Rate limiting
    max_calls_per_session: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Statistics
    total_calls: Mapped[int] = mapped_column(Integer, default=0)
    total_failures: Mapped[int] = mapped_column(Integer, default=0)
    avg_execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Relationships
    agents: Mapped[List["Agent"]] = relationship(
        secondary=agent_tools,
        back_populates="tools"
    )
    
    __table_args__ = (
        Index("ix_agent_tools_category", "category"),
    )


# =============================================================================
# AGENT SESSION MODEL
# =============================================================================

class AgentSession(Base):
    """
    Conversation session with an agent.
    
    Each session tracks:
    - User interaction history
    - Context/memory state
    - Token usage
    - Actions performed
    """
    __tablename__ = "agent_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Session identifier (UUID for external reference)
    session_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    
    # Agent reference
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # User reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Status
    status: Mapped[AgentSessionStatus] = mapped_column(
        Enum(AgentSessionStatus),
        default=AgentSessionStatus.ACTIVE
    )
    
    # Title (auto-generated or user-defined)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Context for this session
    context_project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True
    )
    context_task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Memory state (saved conversation context)
    memory_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Session metrics
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Timing
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()"
    )
    ended_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_activity_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()"
    )
    
    # Client info
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    agent: Mapped["Agent"] = relationship(back_populates="sessions")
    user = relationship("User")
    context_project = relationship("Project")
    context_task = relationship("Task")
    messages: Mapped[List["AgentMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AgentMessage.created_at"
    )
    calls: Mapped[List["AgentCall"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )
    actions: Mapped[List["AgentAction"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("ix_agent_sessions_user", "user_id", "created_at"),
        Index("ix_agent_sessions_agent", "agent_id", "created_at"),
        Index("ix_agent_sessions_status", "status"),
    )


# =============================================================================
# AGENT MESSAGE MODEL
# =============================================================================

class AgentMessage(Base):
    """
    Individual messages in an agent conversation.
    
    Stores both user messages and agent responses.
    """
    __tablename__ = "agent_messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Session reference
    session_id: Mapped[int] = mapped_column(
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Message role (user, assistant, system, tool)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # For tool messages
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tool_args: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tool_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Token counts (for this message)
    tokens_prompt: Mapped[int] = mapped_column(Integer, default=0)
    tokens_completion: Mapped[int] = mapped_column(Integer, default=0)
    
    # Extra data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Feedback
    user_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Processing time
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    session: Mapped["AgentSession"] = relationship(back_populates="messages")
    
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system', 'tool')", name="check_message_role"),
        CheckConstraint("user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5)", name="check_rating_range"),
        Index("ix_agent_messages_session_created", "session_id", "created_at"),
    )


# =============================================================================
# AGENT CALL MODEL
# =============================================================================

class AgentCall(Base):
    """
    Individual LLM API call log.
    
    CRITICAL: Every API call to LLM is logged for:
    - Audit trail
    - Cost tracking
    - Performance monitoring
    - Debugging
    """
    __tablename__ = "agent_calls"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Call identifier
    call_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    
    # Session reference
    session_id: Mapped[int] = mapped_column(
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Agent reference
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # User who triggered
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # LLM Configuration used
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    max_tokens_requested: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Status
    status: Mapped[AgentCallStatus] = mapped_column(
        Enum(AgentCallStatus),
        default=AgentCallStatus.PENDING
    )
    
    # PROMPT INPUT (stored for audit)
    prompt_messages: Mapped[list] = mapped_column(JSON, nullable=False)  # Full message history sent
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    
    # LLM OUTPUT (stored for audit)
    response_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_tool_calls: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timing
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()"
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Cost calculation
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Request metadata
    request_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Relationships
    session: Mapped["AgentSession"] = relationship(back_populates="calls")
    agent = relationship("Agent")
    user = relationship("User")
    
    __table_args__ = (
        Index("ix_agent_calls_status", "status"),
        Index("ix_agent_calls_agent_date", "agent_id", "created_at"),
        Index("ix_agent_calls_user_date", "user_id", "created_at"),
        Index("ix_agent_calls_cost", "cost_usd"),
    )


# =============================================================================
# AGENT ACTION MODEL
# =============================================================================

class AgentAction(Base):
    """
    Actions performed by agents.
    
    Every action an agent takes is logged for:
    - Audit trail
    - Rollback capability
    - Permission verification
    - Security monitoring
    """
    __tablename__ = "agent_actions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Action identifier
    action_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    
    # Session reference
    session_id: Mapped[int] = mapped_column(
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Related call (which LLM call triggered this)
    call_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("agent_calls.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Action type
    action_type: Mapped[AgentActionType] = mapped_column(
        Enum(AgentActionType),
        nullable=False
    )
    
    # Tool used (if applicable)
    tool_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("agent_tools.id", ondelete="SET NULL"),
        nullable=True
    )
    tool_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Status
    status: Mapped[AgentActionStatus] = mapped_column(
        Enum(AgentActionStatus),
        default=AgentActionStatus.PENDING
    )
    
    # Input parameters (for audit)
    input_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Output/result (for audit)
    output_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Affected resources (for rollback)
    affected_resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # task, project, file
    affected_resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # State before action (for rollback)
    previous_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Approval tracking
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Execution timing
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    session: Mapped["AgentSession"] = relationship(back_populates="actions")
    call = relationship("AgentCall")
    tool = relationship("AgentTool")
    approved_by = relationship("User")
    
    __table_args__ = (
        Index("ix_agent_actions_session", "session_id"),
        Index("ix_agent_actions_status", "status"),
        Index("ix_agent_actions_type", "action_type"),
        Index("ix_agent_actions_tool", "tool_name"),
    )


# =============================================================================
# AGENT TASK MODEL (AI-Generated Tasks)
# =============================================================================

class AgentTask(Base):
    """
    Tasks generated by AI agents.
    
    Links AI-generated tasks back to the agent and session.
    """
    __tablename__ = "agent_tasks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Agent reference
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Session that created this task
    session_id: Mapped[int] = mapped_column(
        ForeignKey("agent_sessions.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    
    # Linked task
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Generation context
    prompt_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Confidence score (how confident was the agent)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Review status
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Modifications made by human
    was_modified: Mapped[bool] = mapped_column(Boolean, default=False)
    modification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    agent = relationship("Agent")
    session = relationship("AgentSession")
    task = relationship("Task")
    reviewed_by = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("task_id", name="uq_agent_task"),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="check_confidence_range"
        ),
    )


# =============================================================================
# AGENT COST LOG MODEL
# =============================================================================

class AgentCostLog(Base):
    """
    Detailed cost tracking for AI agent usage.
    
    Aggregated cost logs for billing and monitoring.
    """
    __tablename__ = "agent_cost_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Agent reference
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # User reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Date (for daily aggregation)
    log_date: Mapped[datetime.date] = mapped_column(nullable=False)
    
    # LLM details
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Token usage
    prompt_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    completion_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    total_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # Costs (in USD)
    prompt_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    completion_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Request count
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_request_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Pricing at time of usage
    price_per_1k_prompt_tokens: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_1k_completion_tokens: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationships
    agent = relationship("Agent")
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("agent_id", "user_id", "log_date", "llm_model", name="uq_agent_cost_daily"),
        Index("ix_agent_cost_logs_date", "log_date"),
        Index("ix_agent_cost_logs_agent", "agent_id", "log_date"),
        Index("ix_agent_cost_logs_user", "user_id", "log_date"),
    )
