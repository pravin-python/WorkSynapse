"""
WorkSynapse Chat System Models
==============================
Complete chat system with channels, messages, reactions, and file sharing.

Features:
- Project and direct message channels
- Threaded conversations
- Reactions
- File attachments
- Read receipts
- Typing indicators storage
"""
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, Enum, ForeignKey, Text, Integer, 
    DateTime, Index, UniqueConstraint, CheckConstraint,
    JSON, Table, Column
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin
import enum
import datetime


# =============================================================================
# ENUMS
# =============================================================================

class ChannelType(str, enum.Enum):
    """Channel types."""
    PUBLIC = "PUBLIC"       # Open to all project members
    PRIVATE = "PRIVATE"     # Invite only
    DIRECT = "DIRECT"       # Direct message between users
    PROJECT = "PROJECT"     # Auto-created for project


class MessageType(str, enum.Enum):
    """Message content types."""
    TEXT = "TEXT"
    FILE = "FILE"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    SYSTEM = "SYSTEM"       # System notifications
    CODE = "CODE"           # Code snippet
    LINK = "LINK"


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================

# Many-to-many: Channels <-> Members
channel_members = Table(
    "channel_members",
    Base.metadata,
    Column("channel_id", Integer, ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("joined_at", DateTime(timezone=True), server_default="now()"),
    Column("last_read_message_id", Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True),
    Column("is_muted", Boolean, default=False),
    Column("is_pinned", Boolean, default=False),
)


# =============================================================================
# CHANNEL MODEL
# =============================================================================

class Channel(Base):
    """
    Chat channel for messaging.
    
    Features:
    - Project-scoped or global channels
    - Direct messages between users
    - Member management
    - Last activity tracking
    """
    __tablename__ = "channels"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic info
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Type
    channel_type: Mapped[ChannelType] = mapped_column(
        Enum(ChannelType),
        default=ChannelType.PUBLIC
    )
    
    # Project association (nullable for DMs)
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=True
    )
    
    # Creator
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Settings
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Activity tracking
    last_message_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Appearance
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="channels")
    created_by = relationship("User")
    messages: Mapped[List["Message"]] = relationship(
        back_populates="channel",
        cascade="all, delete-orphan"
    )
    members = relationship(
        "User",
        secondary=channel_members,
        backref="channels"
    )
    pinned_messages: Mapped[List["PinnedMessage"]] = relationship(
        back_populates="channel",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("ix_channels_project", "project_id"),
        Index("ix_channels_type", "channel_type"),
        Index("ix_channels_last_message", "last_message_at"),
    )
    
    def archive(self):
        """Archive the channel."""
        self.is_archived = True
        self.archived_at = datetime.datetime.now(datetime.timezone.utc)
    
    def unarchive(self):
        """Unarchive the channel."""
        self.is_archived = False
        self.archived_at = None


# =============================================================================
# MESSAGE MODEL
# =============================================================================

class Message(Base):
    """
    Chat message with rich content support.
    
    Features:
    - Rich text content
    - File attachments
    - Threading
    - Reactions
    - Edit history
    """
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType),
        default=MessageType.TEXT
    )
    
    # Channel reference
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Sender
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Thread support (reply to message)
    parent_message_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True
    )
    thread_reply_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Edit tracking
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    edited_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # For links, embeds, etc.
    
    # Mentions
    mentions_everyone: Mapped[bool] = mapped_column(Boolean, default=False)
    mentioned_user_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    channel: Mapped["Channel"] = relationship(back_populates="messages")
    sender = relationship("User", back_populates="messages")
    parent_message = relationship("Message", remote_side=[id], backref="thread_replies")
    reactions: Mapped[List["MessageReaction"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan"
    )
    files: Mapped[List["MessageFile"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan"
    )
    read_receipts: Mapped[List["ReadReceipt"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("ix_messages_channel_created", "channel_id", "created_at"),
        Index("ix_messages_sender", "sender_id"),
        Index("ix_messages_parent", "parent_message_id"),
    )


# =============================================================================
# MESSAGE REACTION MODEL
# =============================================================================

class MessageReaction(Base):
    """
    Emoji reactions on messages.
    """
    __tablename__ = "message_reactions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Message reference
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # User who reacted
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Emoji (can be unicode or custom emoji code)
    emoji: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Relationships
    message: Mapped["Message"] = relationship(back_populates="reactions")
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", "emoji", name="uq_message_reaction"),
    )


# =============================================================================
# MESSAGE FILE MODEL
# =============================================================================

class MessageFile(Base):
    """
    File attachments for messages.
    """
    __tablename__ = "message_files"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # File info
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Thumbnail for images/videos
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    # Message reference
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Relationships
    message: Mapped["Message"] = relationship(back_populates="files")
    
    __table_args__ = (
        CheckConstraint("file_size > 0", name="check_message_file_size_positive"),
        CheckConstraint("file_size <= 104857600", name="check_message_file_max_size"),  # 100MB max
    )


# =============================================================================
# READ RECEIPT MODEL
# =============================================================================

class ReadReceipt(Base):
    """
    Read receipts for messages.
    """
    __tablename__ = "read_receipts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Message reference
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # User who read
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # When read
    read_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()"
    )
    
    # Relationships
    message: Mapped["Message"] = relationship(back_populates="read_receipts")
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_read_receipt"),
        Index("ix_read_receipts_user", "user_id"),
    )


# =============================================================================
# PINNED MESSAGE MODEL
# =============================================================================

class PinnedMessage(Base):
    """
    Pinned messages in a channel.
    """
    __tablename__ = "pinned_messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Channel reference
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Message reference
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Who pinned
    pinned_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Relationships
    channel: Mapped["Channel"] = relationship(back_populates="pinned_messages")
    message = relationship("Message")
    pinned_by = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("channel_id", "message_id", name="uq_pinned_message"),
    )
