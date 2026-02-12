"""
WorkSynapse Notes System Models
===============================
Personal and shared notes with rich content and collaboration.

Features:
- Rich text notes
- Folder organization
- Sharing with users
- Tags
"""
from typing import List, Optional
from sqlalchemy import (
    String, Boolean, Enum, ForeignKey, Text, Integer, 
    DateTime, Index, UniqueConstraint, Table, Column, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.base import Base, AuditMixin
import enum
import datetime


# =============================================================================
# ENUMS
# =============================================================================

class SharePermission(str, enum.Enum):
    """Note share permissions."""
    VIEW = "VIEW"
    EDIT = "EDIT"


class NoteVisibility(str, enum.Enum):
    """Visibility for notes (matches DB enum `notevisibility`)."""
    PRIVATE = "PRIVATE"
    SHARED = "SHARED"
    PROJECT = "PROJECT"
    ORGANIZATION = "ORGANIZATION"


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================

# Many-to-many: Notes <-> Tags
# Association table: note_tags (maps notes to tag definitions)
note_tag_map = Table(
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
    
    # Appearance
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # Created At
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    # Ordering
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    owner = relationship("User")
    notes: Mapped[List["Note"]] = relationship(
        back_populates="folder"
    )
    
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_folder_owner_name"),
        Index("ix_note_folders_owner", "owner_id"),
    )


# =============================================================================
# NOTE TAG MODEL
# =============================================================================

class NoteTag(Base):
    """
    Tag definitions for notes.
    """
    __tablename__ = "note_tag_definitions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Tag info
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Owner
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    
    # Relationships
    owner = relationship("User")
    notes: Mapped[List["Note"]] = relationship(
        secondary=note_tag_map,
        back_populates="tags"
    )
    
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_tag_owner_name"),
    )


# =============================================================================
# NOTE MODEL
# =============================================================================

class Note(Base, AuditMixin):
    """
    Personal or shared note with rich content.
    """
    __tablename__ = "notes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Content
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
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

    # Optional link to a project
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    
    # Visibility enum (DB requires non-null)
    visibility: Mapped[NoteVisibility] = mapped_column(
        Enum(NoteVisibility, name="notevisibility"),
        default=NoteVisibility.PRIVATE,
        nullable=False,
    )
    
    # Status
    # Database column is `is_pinned` (keeps compatibility with migrations).
    is_pinned: Mapped[bool] = mapped_column(Boolean, name="is_pinned", default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    template_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    search_vector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    @hybrid_property
    def is_starred(self) -> bool:
        return self.is_pinned

    @is_starred.expression
    def is_starred(cls):
        return cls.is_pinned

    @is_starred.setter
    def is_starred(self, value: bool):
        self.is_pinned = value
        
    # Timestamps (AuditMixin handles created_at/updated_at but we can be explicit if needed)
    
    # Relationships
    owner = relationship("User", back_populates="notes", foreign_keys=[owner_id])
    folder: Mapped[Optional["NoteFolder"]] = relationship(back_populates="notes")
    shares: Mapped[List["NoteShare"]] = relationship(
        back_populates="note",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    tags: Mapped[List["NoteTag"]] = relationship(
        secondary=note_tag_map,
        back_populates="notes",
        lazy="selectin"
    )
    project: Mapped[Optional["Project"]] = relationship(back_populates="notes", lazy="selectin")
    
    __table_args__ = (
        Index("ix_notes_owner", "owner_id"),
        Index("ix_notes_starred", "owner_id", "is_pinned"),
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
    
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    
    # Relationships
    note: Mapped["Note"] = relationship(back_populates="shares")
    shared_with = relationship("User", foreign_keys=[shared_with_user_id])
    shared_by = relationship("User", foreign_keys=[shared_by_user_id])
    
    __table_args__ = (
        UniqueConstraint("note_id", "shared_with_user_id", name="uq_note_share"),
    )

