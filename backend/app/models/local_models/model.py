"""
Local Model Registry Models
===========================

SQLAlchemy models for local AI model management.
Supports HuggingFace, Ollama, and custom local LLMs.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, AuditMixin


class ModelSource(str, Enum):
    """Source of the local model."""
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class ModelStatus(str, Enum):
    """Download/availability status of the model."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    READY = "ready"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelType(str, Enum):
    """Type of AI model."""
    TEXT_GENERATION = "text-generation"
    TEXT2TEXT = "text2text-generation"
    CHAT = "chat"
    EMBEDDING = "embedding"
    IMAGE_GENERATION = "image-generation"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"
    OTHER = "other"


class LocalModel(Base, AuditMixin):
    """
    Local AI Model Registry.
    
    Stores information about downloaded or available local models
    from various sources (HuggingFace, Ollama, Custom).
    """
    __tablename__ = "local_models"
    __table_args__ = (
        Index('ix_local_models_source_status', 'source', 'status'),
        Index('ix_local_models_model_id', 'model_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Model identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    source: Mapped[ModelSource] = mapped_column(
        SQLEnum(ModelSource, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ModelSource.HUGGINGFACE
    )
    model_type: Mapped[ModelType] = mapped_column(
        SQLEnum(ModelType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ModelType.TEXT_GENERATION
    )
    
    # Model metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    license: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    
    # Storage information
    local_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Download status
    status: Mapped[ModelStatus] = mapped_column(
        SQLEnum(ModelStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ModelStatus.PENDING
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Celery task tracking
    task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Download metadata
    downloaded_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    download_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    download_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Usage tracking
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Model parameters (for configuration)
    default_params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    
    # Relationships
    downloaded_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[downloaded_by],
        backref="downloaded_models"
    )

    def __repr__(self):
        return f"<LocalModel {self.name} ({self.source.value})>"
    
    @property
    def size_mb(self) -> float:
        """Return size in MB."""
        if self.size_bytes:
            return round(self.size_bytes / (1024 * 1024), 2)
        return 0.0
    
    @property
    def size_gb(self) -> float:
        """Return size in GB."""
        if self.size_bytes:
            return round(self.size_bytes / (1024 * 1024 * 1024), 2)
        return 0.0
    
    @property
    def is_downloading(self) -> bool:
        """Check if model is currently downloading."""
        return self.status == ModelStatus.DOWNLOADING
    
    @property
    def is_ready(self) -> bool:
        """Check if model is ready to use."""
        return self.status == ModelStatus.READY


class ModelDownloadLog(Base, AuditMixin):
    """
    Log of model download attempts and events.
    """
    __tablename__ = "model_download_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("local_models.id", ondelete="CASCADE"),
        nullable=False
    )
    
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    progress: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bytes_downloaded: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationship
    model: Mapped["LocalModel"] = relationship("LocalModel", backref="download_logs")

    def __repr__(self):
        return f"<ModelDownloadLog {self.event_type} for model {self.model_id}>"
