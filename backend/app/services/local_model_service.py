"""
Local Model Service
===================

Business logic for local model management, downloads, and integration.
"""

import os
import json
import shutil
import asyncio
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.local_models.model import (
    LocalModel, ModelDownloadLog,
    ModelSource, ModelStatus, ModelType
)
from app.schemas.local_models import (
    LocalModelCreate, LocalModelUpdate,
    HuggingFaceModelInfo, OllamaModelInfo
)
from app.core.config import settings


class LocalModelServiceError(Exception):
    """Service-level error."""
    pass


# Storage paths
MODELS_BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "models"
)


def get_model_storage_path(source: ModelSource, model_id: str) -> str:
    """Get storage path for a model."""
    # Sanitize model_id for filesystem
    safe_model_id = model_id.replace("/", "--").replace("\\", "--")
    return os.path.join(MODELS_BASE_PATH, source.value, safe_model_id)


def ensure_storage_directories():
    """Ensure model storage directories exist."""
    for source in ModelSource:
        path = os.path.join(MODELS_BASE_PATH, source.value)
        os.makedirs(path, exist_ok=True)


class LocalModelService:
    """Service for managing local AI models."""
    
    # ============================================
    # CRUD OPERATIONS
    # ============================================
    
    @staticmethod
    async def get_models(
        db: AsyncSession,
        source: Optional[ModelSource] = None,
        status: Optional[ModelStatus] = None,
        ready_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[LocalModel], int]:
        """Get all local models with optional filters."""
        query = select(LocalModel)
        count_query = select(func.count(LocalModel.id))
        
        if source:
            query = query.where(LocalModel.source == source)
            count_query = count_query.where(LocalModel.source == source)
        
        if status:
            query = query.where(LocalModel.status == status)
            count_query = count_query.where(LocalModel.status == status)
        
        if ready_only:
            query = query.where(LocalModel.status == ModelStatus.READY)
            count_query = count_query.where(LocalModel.status == ModelStatus.READY)
        
        query = query.order_by(LocalModel.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        models = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return models, total
    
    @staticmethod
    async def get_model(db: AsyncSession, model_id: int) -> Optional[LocalModel]:
        """Get a model by ID."""
        result = await db.execute(
            select(LocalModel).where(LocalModel.id == model_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_model_by_model_id(db: AsyncSession, model_id: str) -> Optional[LocalModel]:
        """Get a model by its source model ID."""
        result = await db.execute(
            select(LocalModel).where(LocalModel.model_id == model_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_model(
        db: AsyncSession,
        data: LocalModelCreate,
        user_id: Optional[int] = None
    ) -> LocalModel:
        """Create a new local model entry."""
        # Check if model already exists
        existing = await LocalModelService.get_model_by_model_id(db, data.model_id)
        if existing:
            raise LocalModelServiceError(f"Model {data.model_id} already registered")
        
        model = LocalModel(
            name=data.name,
            model_id=data.model_id,
            source=ModelSource(data.source),
            model_type=ModelType(data.model_type),
            description=data.description,
            local_path=data.local_path,
            size_bytes=data.size_bytes,
            default_params=json.dumps(data.default_params) if data.default_params else None,
            status=ModelStatus.READY if data.local_path else ModelStatus.PENDING,
            downloaded_by=user_id
        )
        
        db.add(model)
        await db.commit()
        await db.refresh(model)
        return model
    
    @staticmethod
    async def update_model(
        db: AsyncSession,
        model_id: int,
        data: LocalModelUpdate
    ) -> Optional[LocalModel]:
        """Update a model."""
        model = await LocalModelService.get_model(db, model_id)
        if not model:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "default_params" and value is not None:
                value = json.dumps(value)
            setattr(model, field, value)
        
        await db.commit()
        await db.refresh(model)
        return model
    
    @staticmethod
    async def delete_model(db: AsyncSession, model_id: int) -> bool:
        """Delete a model and its files."""
        model = await LocalModelService.get_model(db, model_id)
        if not model:
            return False
        
        # Don't delete if currently downloading
        if model.status == ModelStatus.DOWNLOADING:
            raise LocalModelServiceError("Cannot delete a model that is currently downloading")
        
        # Delete local files if they exist
        if model.local_path and os.path.exists(model.local_path):
            try:
                shutil.rmtree(model.local_path)
            except Exception as e:
                raise LocalModelServiceError(f"Failed to delete model files: {str(e)}")
        
        await db.delete(model)
        await db.commit()
        return True
    
    # ============================================
    # DOWNLOAD MANAGEMENT
    # ============================================
    
    @staticmethod
    async def initiate_download(
        db: AsyncSession,
        model_id: str,
        source: ModelSource,
        model_type: ModelType,
        user_id: int,
        model_info: Optional[dict] = None
    ) -> LocalModel:
        """
        Initiate a model download.
        
        Creates the model entry and returns it.
        The actual download is handled by Celery task.
        """
        # Check if already exists
        existing = await LocalModelService.get_model_by_model_id(db, model_id)
        if existing:
            if existing.status == ModelStatus.READY:
                raise LocalModelServiceError("Model is already downloaded")
            if existing.status == ModelStatus.DOWNLOADING:
                raise LocalModelServiceError("Model is currently downloading")
            # If failed or cancelled, we can retry
            existing.status = ModelStatus.PENDING
            existing.progress = 0.0
            existing.error_message = None
            await db.commit()
            return existing
        
        # Extract name from model_id
        name = model_id.split("/")[-1] if "/" in model_id else model_id
        
        # Create model entry
        model = LocalModel(
            name=name,
            model_id=model_id,
            source=source,
            model_type=model_type,
            description=model_info.get("description") if model_info else None,
            author=model_info.get("author") if model_info else None,
            tags=json.dumps(model_info.get("tags", [])) if model_info else None,
            status=ModelStatus.PENDING,
            progress=0.0,
            downloaded_by=user_id,
            local_path=get_model_storage_path(source, model_id)
        )
        
        db.add(model)
        await db.commit()
        await db.refresh(model)
        return model
    
    @staticmethod
    async def update_download_status(
        db: AsyncSession,
        model_id: int,
        status: ModelStatus,
        progress: float = 0.0,
        error_message: Optional[str] = None,
        task_id: Optional[str] = None,
        size_bytes: Optional[int] = None
    ) -> Optional[LocalModel]:
        """Update download status of a model."""
        model = await LocalModelService.get_model(db, model_id)
        if not model:
            return None
        
        model.status = status
        model.progress = progress
        
        if error_message:
            model.error_message = error_message
        
        if task_id:
            model.task_id = task_id
        
        if size_bytes:
            model.size_bytes = size_bytes
        
        if status == ModelStatus.DOWNLOADING and not model.download_started_at:
            model.download_started_at = datetime.utcnow()
        
        if status == ModelStatus.READY:
            model.download_completed_at = datetime.utcnow()
            model.progress = 100.0
        
        await db.commit()
        await db.refresh(model)
        return model
    
    @staticmethod
    async def cancel_download(db: AsyncSession, model_id: int) -> bool:
        """Cancel a model download."""
        model = await LocalModelService.get_model(db, model_id)
        if not model:
            return False
        
        if model.status != ModelStatus.DOWNLOADING:
            raise LocalModelServiceError("Model is not currently downloading")
        
        # Cancel Celery task if exists
        if model.task_id:
            from app.core.celery_app import celery_app
            celery_app.control.revoke(model.task_id, terminate=True)
        
        model.status = ModelStatus.CANCELLED
        model.error_message = "Download cancelled by user"
        
        # Clean up partial download
        if model.local_path and os.path.exists(model.local_path):
            try:
                shutil.rmtree(model.local_path)
            except Exception:
                pass
        
        await db.commit()
        return True
    
    @staticmethod
    async def log_download_event(
        db: AsyncSession,
        model_id: int,
        event_type: str,
        message: Optional[str] = None,
        progress: Optional[float] = None,
        bytes_downloaded: Optional[int] = None
    ):
        """Log a download event."""
        log = ModelDownloadLog(
            model_id=model_id,
            event_type=event_type,
            message=message,
            progress=progress,
            bytes_downloaded=bytes_downloaded
        )
        db.add(log)
        await db.commit()
    
    # ============================================
    # STATISTICS
    # ============================================
    
    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        """Get model statistics."""
        # Count by status
        result = await db.execute(
            select(
                LocalModel.status,
                func.count(LocalModel.id)
            ).group_by(LocalModel.status)
        )
        status_counts = {row[0].value: row[1] for row in result.all()}
        
        # Total size
        size_result = await db.execute(
            select(func.sum(LocalModel.size_bytes)).where(
                LocalModel.status == ModelStatus.READY
            )
        )
        total_size = size_result.scalar() or 0
        
        # Disk space
        disk_stats = shutil.disk_usage(MODELS_BASE_PATH if os.path.exists(MODELS_BASE_PATH) else "/")
        
        return {
            "total_models": sum(status_counts.values()),
            "ready_models": status_counts.get("ready", 0),
            "downloading_models": status_counts.get("downloading", 0),
            "failed_models": status_counts.get("failed", 0),
            "total_size_gb": round(total_size / (1024**3), 2),
            "disk_free_gb": round(disk_stats.free / (1024**3), 2),
            "disk_used_percent": round((disk_stats.used / disk_stats.total) * 100, 1)
        }
    
    # ============================================
    # AGENT INTEGRATION
    # ============================================
    
    @staticmethod
    async def get_models_for_agent(
        db: AsyncSession,
        source: Optional[ModelSource] = None
    ) -> List[LocalModel]:
        """Get ready models available for agent binding."""
        query = select(LocalModel).where(
            LocalModel.status == ModelStatus.READY,
            LocalModel.is_active == True
        )
        
        if source:
            query = query.where(LocalModel.source == source)
        
        query = query.order_by(LocalModel.name)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def record_model_usage(db: AsyncSession, model_id: int):
        """Record that a model was used."""
        model = await LocalModelService.get_model(db, model_id)
        if model:
            model.usage_count += 1
            model.last_used_at = datetime.utcnow()
            await db.commit()


# Initialize storage directories on import
ensure_storage_directories()


# Singleton instance
local_model_service = LocalModelService()
