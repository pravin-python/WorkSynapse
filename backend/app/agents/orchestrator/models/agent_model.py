"""
Agent SQLAlchemy Models
=======================

Database models for storing agent configurations and execution history.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Text,
    Boolean,
    Integer,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
import enum

from app.models.base import Base


class LLMProvider(str, enum.Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    CLAUDE = "claude"
    HUGGINGFACE = "huggingface"


class MemoryType(str, enum.Enum):
    """Supported memory types."""

    CONVERSATION = "conversation"
    VECTOR = "vector"
    SESSION = "session"
    NONE = "none"


class ExecutionStatus(str, enum.Enum):
    """Execution status states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Agent(Base):
    """
    Agent model representing a dynamically created AI agent.

    Each agent has its own configuration including:
    - System prompt and goal
    - LLM provider and model selection
    - Tool assignments
    - Memory configuration
    - Permission settings
    """

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Agent identity
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Agent behavior
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    identity_guidance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # LLM configuration
    llm_provider: Mapped[str] = mapped_column(
        String(50), default=LLMProvider.OPENAI.value
    )
    model_name: Mapped[str] = mapped_column(String(100), default="gpt-4o")
    temperature: Mapped[float] = mapped_column(default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    
    # Tools configuration (JSON array of tool configs)
    tools: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=list)
    
    # Memory configuration
    memory_type: Mapped[str] = mapped_column(
        String(50), default=MemoryType.CONVERSATION.value
    )
    enable_long_term_memory: Mapped[bool] = mapped_column(Boolean, default=False)
    memory_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Permissions and security
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Advanced configuration
    config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Agent flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_planning: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_reasoning: Mapped[bool] = mapped_column(Boolean, default=True)
    can_stop_itself: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    
    # Reverse relationships
    conversations: Mapped[List["AgentConversation"]] = relationship(
        "AgentConversation", back_populates="agent", cascade="all, delete-orphan"
    )
    executions: Mapped[List["AgentExecution"]] = relationship(
        "AgentExecution", back_populates="agent", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name='{self.name}', provider='{self.llm_provider}')>"

    def get_tools_list(self) -> List[str]:
        """Get list of tool names assigned to this agent."""
        if isinstance(self.tools, list):
            return [
                t.get("name") if isinstance(t, dict) else t
                for t in self.tools
            ]
        return []

    def has_permission(self, permission: str) -> bool:
        """Check if agent has a specific permission."""
        return self.permissions.get(permission, False)


class AgentConversation(Base):
    """
    Conversation model for tracking agent chat sessions.

    Each conversation has:
    - A unique thread ID for LangGraph checkpointing
    - Message history
    - Associated metadata
    """

    __tablename__ = "agent_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    agent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    
    # Thread identifier for LangGraph
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True
    )
    
    # Conversation data
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    messages: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="conversations")
    executions: Mapped[List["AgentExecution"]] = relationship(
        "AgentExecution", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AgentConversation(id={self.id}, thread='{self.thread_id}')>"

    def add_message(self, role: str, content: str, **kwargs):
        """Add a message to the conversation history."""
        message = {"role": role, "content": content, **kwargs}
        if self.messages is None:
            self.messages = []
        self.messages.append(message)

    def get_message_count(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self.messages) if self.messages else 0


class AgentExecution(Base):
    """
    Execution model for tracking individual agent invocations.

    Records:
    - Input/output messages
    - Tool calls made
    - Token usage
    - Execution timing
    - Error information
    """

    __tablename__ = "agent_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    agent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("agent_conversations.id", ondelete="SET NULL"), nullable=True
    )
    
    # User who triggered execution
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    
    # Execution data
    input_message: Mapped[str] = mapped_column(Text, nullable=False)
    output_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tool usage
    tool_calls: Mapped[List[Dict[str, Any]]] = mapped_column(JSONB, default=list)
    
    # Usage metrics
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    tokens_total: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    
    # Execution status
    status: Mapped[str] = mapped_column(
        String(50), default=ExecutionStatus.PENDING.value, index=True
    )
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Additional metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="executions")
    conversation: Mapped[Optional["AgentConversation"]] = relationship(
        "AgentConversation", back_populates="executions"
    )

    def __repr__(self) -> str:
        return f"<AgentExecution(id={self.id}, status='{self.status}')>"

    def mark_completed(self, output: str, tokens: dict = None, duration_ms: int = 0):
        """Mark execution as completed with results."""
        self.output_message = output
        self.status = ExecutionStatus.COMPLETED.value
        self.duration_ms = duration_ms
        if tokens:
            self.tokens_input = tokens.get("input", 0)
            self.tokens_output = tokens.get("output", 0)
            self.tokens_total = tokens.get("total", 0)

    def mark_failed(self, error: str):
        """Mark execution as failed with error message."""
        self.status = ExecutionStatus.FAILED.value
        self.error = error

    def add_tool_call(self, tool_name: str, args: dict, result: Any):
        """Record a tool call made during execution."""
        if self.tool_calls is None:
            self.tool_calls = []
        self.tool_calls.append({
            "tool": tool_name,
            "args": args,
            "result": str(result) if result else None,
        })
