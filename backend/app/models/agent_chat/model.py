"""
WorkSynapse Agent Chat Models
==============================
Database models for agent conversations, messages, and file attachments.
Separate from the team chat system — these power AI agent interactions.
"""
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, Enum, ForeignKey, Text, Integer,
    DateTime, Index, BigInteger, Float, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import enum
import datetime
import uuid


# =============================================================================
# ENUMS
# =============================================================================

class AgentChatSenderType(str, enum.Enum):
    """Who sent the message."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class AgentChatMessageType(str, enum.Enum):
    """Type of message content."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    PDF = "pdf"


# =============================================================================
# AGENT CONVERSATION
# =============================================================================

class AgentConversation(Base):
    """
    A conversation session between a user and an AI agent.
    Each conversation has its own message history and thread context.
    """
    __tablename__ = "agent_conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Agent reference
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # User who started the conversation
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # Conversation metadata
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    thread_id: Mapped[str] = mapped_column(
        String(36),
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        index=True
    )

    # Status
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    # Activity tracking
    last_message_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    agent = relationship("CustomAgent", backref="conversations")
    user = relationship("User", backref="agent_conversations")
    messages: Mapped[List["AgentChatMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AgentChatMessage.created_at"
    )

    __table_args__ = (
        Index("ix_agent_conv_agent_user", "agent_id", "user_id"),
        Index("ix_agent_conv_last_msg", "last_message_at"),
    )

    def __repr__(self):
        return f"<AgentConversation(id={self.id}, agent_id={self.agent_id}, title='{self.title}')>"


# =============================================================================
# AGENT CHAT MESSAGE
# =============================================================================

class AgentChatMessage(Base):
    """
    A single message in an agent conversation.
    Can be from the user, agent, or system.
    """
    __tablename__ = "agent_chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Conversation reference
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # Sender
    sender_type: Mapped[AgentChatSenderType] = mapped_column(
        Enum(AgentChatSenderType),
        nullable=False
    )

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[AgentChatMessageType] = mapped_column(
        Enum(AgentChatMessageType),
        default=AgentChatMessageType.TEXT
    )

    # Token tracking (for agent messages)
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    tokens_total: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    # Tool calls metadata (for agent messages)
    tool_calls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Extra metadata (renamed from 'metadata' to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    conversation: Mapped["AgentConversation"] = relationship(back_populates="messages")
    files: Mapped[List["AgentChatFile"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_agent_msg_conv_created", "conversation_id", "created_at"),
        Index("ix_agent_msg_sender", "sender_type"),
    )

    def __repr__(self):
        return f"<AgentChatMessage(id={self.id}, sender={self.sender_type.value}, type={self.message_type.value})>"


# =============================================================================
# AGENT CHAT FILE
# =============================================================================

class AgentChatFile(Base):
    """
    File attachment for an agent chat message.
    Files are stored in backend/media/chat_uploads/{conversation_id}/
    """
    __tablename__ = "agent_chat_files"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Message reference
    message_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("agent_chat_messages.id", ondelete="CASCADE"),
        index=True,
        nullable=True  # nullable to allow uploading before message is created
    )

    # Conversation reference (for file organization)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # Uploader
    uploaded_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    # File info
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)  # MIME type
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes

    # Thumbnail for images
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # RAG integration
    is_rag_ingested: Mapped[bool] = mapped_column(Boolean, default=False)
    rag_document_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("rag_documents.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    message: Mapped[Optional["AgentChatMessage"]] = relationship(back_populates="files")

    def __repr__(self):
        return f"<AgentChatFile(id={self.id}, name='{self.file_name}', size={self.file_size})>"
