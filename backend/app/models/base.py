"""
WorkSynapse Base Model
======================
Enhanced base model with soft delete, timestamp tracking, and audit support.
"""
from typing import Any, Optional
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, Boolean, func, event, String
import datetime
import uuid


class Base(DeclarativeBase):
    """
    Base model for all WorkSynapse tables.
    
    Features:
    - Auto-generated table names
    - Created/Updated timestamps
    - Soft delete support
    - UUID primary keys option
    """
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'

    # Timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # Soft delete support
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        nullable=False,
        index=True
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    def soft_delete(self):
        """Mark record as deleted without removing from database."""
        self.is_deleted = True
        self.deleted_at = datetime.datetime.now(datetime.timezone.utc)
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class TimestampMixin:
    """Mixin for models that only need timestamps without soft delete."""
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )


class AuditMixin:
    """Mixin for enhanced audit logging on sensitive tables."""
    
    @declared_attr
    def created_by_user_id(cls) -> Mapped[Optional[int]]:
        from sqlalchemy import ForeignKey
        return mapped_column(
            ForeignKey("users.id"), 
            nullable=True,
            index=True
        )
    
    @declared_attr
    def updated_by_user_id(cls) -> Mapped[Optional[int]]:
        from sqlalchemy import ForeignKey
        return mapped_column(
            ForeignKey("users.id"), 
            nullable=True
        )
    
    last_modified_ip: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True
    )


def generate_uuid() -> str:
    """Generate a UUID string for use as identifier."""
    return str(uuid.uuid4())
