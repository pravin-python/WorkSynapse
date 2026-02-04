"""
WorkSynapse Notes System Models
===============================
Personal and shared notes with rich content and collaboration.

Features:
- Rich text notes
- Folder organization
- Sharing with users and projects
- Version history
- Tags
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

class NoteVisibility(str, enum.Enum):
    """Note visibility settings."""
    PRIVATE = "PRIVATE"         # Only owner
    SHARED = "SHARED"           # Specific users
    PROJECT = "PROJECT"         # All project members
    ORGANIZATION = "ORGANIZATION"


class SharePermission(str, enum.Enum):
    """Note share permissions."""
    VIEW = "VIEW"
    COMMENT = "COMMENT"
    EDIT = "EDIT"


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================

# Many-to-many: Notes <-> Tags
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("note_tag_definitions.id", ondelete="CASCADE"), primary_key=True),
)


# =============================================================================
# NOTE FOLDER MODEL
# =============================================================================

class NoteFolder(Base):
    """
    Folder for organizing notes.
    """
    __tablename__ = "note_folders"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Owner
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Parent folder (for nesting)
    parent_folder_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("note_folders.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Appearance
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Position for ordering
    position: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    owner = relationship("User")
    parent_folder = relationship("NoteFolder", remote_side=[id], backref="child_folders")
    notes: Mapped[List["Note"]] = relationship(
        back_populates="folder"
    )
    
    __table_args__ = (
        UniqueConstraint("owner_id", "parent_folder_id", "name", name="uq_folder_name"),
        Index("ix_note_folders_owner", "owner_id"),
    )


# =============================================================================
# NOTE MODEL
# =============================================================================

class Note(Base, AuditMixin):
    """
    Personal or shared note with rich content.
    
    Features:
    - Rich text content (stored as JSON for blocks)
    - Project association
    - Folder organization
    - Version history
    """
    __tablename__ = "notes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Content (can be plain text or rich JSON)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # For rich editor blocks
    
    # Excerpt for preview
    excerpt: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Owner
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Organization
    folder_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("note_folders.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    
    # Project association (optional)
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=True
    )
    
    # Visibility
    visibility: Mapped[NoteVisibility] = mapped_column(
        Enum(NoteVisibility),
        default=NoteVisibility.PRIVATE
    )
    
    # Status
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Template
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    template_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Version tracking
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Full-text search
    search_vector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For FTS indexing
    
    # Relationships
    owner = relationship("User", back_populates="notes", foreign_keys=[owner_id])
    folder: Mapped[Optional["NoteFolder"]] = relationship(back_populates="notes")
    project = relationship("Project", back_populates="notes")
    shares: Mapped[List["NoteShare"]] = relationship(
        back_populates="note",
        cascade="all, delete-orphan"
    )
    versions: Mapped[List["NoteVersion"]] = relationship(
        back_populates="note",
        cascade="all, delete-orphan"
    )
    tags: Mapped[List["NoteTagDefinition"]] = relationship(
        secondary=note_tags,
        back_populates="notes"
    )
    comments: Mapped[List["NoteComment"]] = relationship(
        back_populates="note",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("ix_notes_owner", "owner_id"),
        Index("ix_notes_project", "project_id"),
        Index("ix_notes_visibility", "visibility"),
        Index("ix_notes_pinned", "owner_id", "is_pinned"),
    )


# =============================================================================
# NOTE SHARE MODEL
# =============================================================================

class NoteShare(Base):
    """
    Note sharing with specific users.
    """
    __tablename__ = "note_shares"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Note reference
    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Shared with user
    shared_with_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Permission level
    permission: Mapped[SharePermission] = mapped_column(
        Enum(SharePermission),
        default=SharePermission.VIEW
    )
    
    # Shared by
    shared_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Share expiration (optional)
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Access tracking
    last_accessed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    note: Mapped["Note"] = relationship(back_populates="shares")
    shared_with = relationship("User", foreign_keys=[shared_with_user_id])
    shared_by = relationship("User", foreign_keys=[shared_by_user_id])
    
    __table_args__ = (
        UniqueConstraint("note_id", "shared_with_user_id", name="uq_note_share"),
    )
    
    def is_valid(self) -> bool:
        """Check if share is still valid."""
        if self.expires_at is None:
            return True
        return datetime.datetime.now(datetime.timezone.utc) < self.expires_at


# =============================================================================
# NOTE VERSION MODEL
# =============================================================================

class NoteVersion(Base):
    """
    Note version history for tracking changes.
    """
    __tablename__ = "note_versions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Note reference
    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Version number
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Snapshot
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Who made the change
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Change summary
    change_summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    note: Mapped["Note"] = relationship(back_populates="versions")
    created_by = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("note_id", "version_number", name="uq_note_version"),
        Index("ix_note_versions_note", "note_id", "version_number"),
    )


# =============================================================================
# NOTE TAG DEFINITION MODEL
# =============================================================================

class NoteTagDefinition(Base):
    """
    Tag definitions for notes.
    """
    __tablename__ = "note_tag_definitions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Tag info
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # Owner (for personal tags) or null (for system tags)
    owner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True
    )
    
    # Usage count (for popularity)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    owner = relationship("User")
    notes: Mapped[List["Note"]] = relationship(
        secondary=note_tags,
        back_populates="tags"
    )
    
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_tag_owner_name"),
    )


# =============================================================================
# NOTE COMMENT MODEL
# =============================================================================

class NoteComment(Base):
    """
    Comments on notes.
    """
    __tablename__ = "note_comments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Note reference
    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Author
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Position in document (for inline comments)
    position_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    position_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Reply to another comment
    parent_comment_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("note_comments.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Resolved status
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolved_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Relationships
    note: Mapped["Note"] = relationship(back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])
    parent_comment = relationship("NoteComment", remote_side=[id], backref="replies")
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])
    
    __table_args__ = (
        Index("ix_note_comments_note", "note_id"),
    )
