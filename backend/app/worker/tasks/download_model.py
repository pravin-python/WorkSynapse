"""
Model Download Celery Tasks
===========================

Background tasks for downloading AI models from various sources.
Uses Celery for async processing to avoid blocking Uvicorn.
"""

import os
import json
import time
import shutil
import asyncio
from datetime import datetime
from typing import Optional, Callable
from celery import shared_task
from celery.exceptions import Ignore, SoftTimeLimitExceeded

from app.core.celery_app import celery_app

from app.models.local_models.model import LocalModel, ModelSource, ModelStatus
from app.services.websocket_manager import manager


# Storage base path
MODELS_BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "models"
)


def get_sync_db():
    """Get synchronous database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    
    # Create sync engine from async URL
    sync_url = str(settings.DATABASE_URL).replace("+asyncpg", "")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    return Session()


def update_model_status_sync(
    model_id: int,
    status: ModelStatus,
    progress: float = 0.0,
    error_message: Optional[str] = None,
    size_bytes: Optional[int] = None
):
    """Synchronously update model status (for Celery tasks)."""
    db = get_sync_db()
    try:
        model = db.query(LocalModel).filter(LocalModel.id == model_id).first()
        if model:
            model.status = status
            model.progress = progress
            if error_message:
                model.error_message = error_message
            if size_bytes:
                model.size_bytes = size_bytes
            if status == ModelStatus.DOWNLOADING and not model.download_started_at:
                model.download_started_at = datetime.utcnow()
            if status == ModelStatus.READY:
                model.download_completed_at = datetime.utcnow()
                model.progress = 100.0
            db.commit()
    finally:
        db.close()


def send_progress_update(model_id: int, progress: float, status: str, message: Optional[str] = None):
    """Send progress update via WebSocket (sync version)."""
    channel = f"model-download-{model_id}"
    data = {
        "model_id": model_id,
        "progress": round(progress, 2),
        "status": status,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    # We'll use Redis pub/sub for cross-process WebSocket updates
    try:
        import redis
        from app.core.config import settings
        r = redis.from_url(settings.REDIS_URL)
        r.publish(f"ws:{channel}", json.dumps(data))
    except Exception:
        pass  # Silently fail if Redis unavailable


@celery_app.task(
    bind=True,
    name="app.worker.tasks.download_model.download_huggingface_model",
    acks_late=True,
    max_retries=2,
    soft_time_limit=7200,  # 2 hours
    time_limit=7500  # 2.5 hours hard limit
)
def download_huggingface_model(self, model_db_id: int, model_id: str, target_path: str):
    """
    Download a model from HuggingFace Hub.
    
    Args:
        model_db_id: Database ID of the LocalModel
        model_id: HuggingFace model ID (e.g., 'meta-llama/Llama-3.1-8B-Instruct')
        target_path: Local path to save the model
    """
    try:
        # Update status to downloading
        update_model_status_sync(model_db_id, ModelStatus.DOWNLOADING, 0.0)
        send_progress_update(model_db_id, 0.0, "downloading", "Starting download...")
        
        # Ensure target directory exists
        os.makedirs(target_path, exist_ok=True)
        
        # Import huggingface_hub
        try:
            from huggingface_hub import snapshot_download, HfApi
        except ImportError:
            raise Exception("huggingface_hub not installed. Run: pip install huggingface_hub")
        
        # Get model info first
        api = HfApi()
        try:
            model_info = api.model_info(model_id)
            # Estimate size from siblings if available
            total_size = sum(
                getattr(s, 'size', 0) or 0 
                for s in getattr(model_info, 'siblings', [])
            )
        except Exception:
            total_size = 0
        
        # Track download progress
        downloaded_bytes = 0
        last_update = time.time()
        
        def progress_callback(progress_info):
            nonlocal downloaded_bytes, last_update
            
            # Rate limit updates to every 2 seconds
            current_time = time.time()
            if current_time - last_update < 2:
                return
            last_update = current_time
            
            # Calculate progress
            if hasattr(progress_info, 'downloaded'):
                downloaded_bytes = progress_info.downloaded
            
            if total_size > 0:
                percent = min((downloaded_bytes / total_size) * 100, 99)
            else:
                percent = 50  # Indeterminate
            
            update_model_status_sync(model_db_id, ModelStatus.DOWNLOADING, percent)
            send_progress_update(
                model_db_id, 
                percent, 
                "downloading",
                f"Downloaded {downloaded_bytes / (1024**3):.2f} GB"
            )
        
        # Download the model
        send_progress_update(model_db_id, 5.0, "downloading", "Connecting to HuggingFace...")
        
        local_dir = snapshot_download(
            repo_id=model_id,
            local_dir=target_path,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        # Calculate actual size
        actual_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, dirnames, filenames in os.walk(target_path)
            for filename in filenames
        )
        
        # Update as complete
        update_model_status_sync(
            model_db_id, 
            ModelStatus.READY, 
            100.0, 
            size_bytes=actual_size
        )
        send_progress_update(model_db_id, 100.0, "ready", "Download complete!")
        
        return {
            "status": "success",
            "model_id": model_db_id,
            "path": target_path,
            "size_bytes": actual_size
        }
        
    except SoftTimeLimitExceeded:
        update_model_status_sync(
            model_db_id, 
            ModelStatus.FAILED, 
            error_message="Download timed out after 2 hours"
        )
        send_progress_update(model_db_id, 0, "failed", "Download timed out")
        raise Ignore()
        
    except Exception as e:
        error_msg = str(e)
        update_model_status_sync(
            model_db_id, 
            ModelStatus.FAILED, 
            error_message=error_msg
        )
        send_progress_update(model_db_id, 0, "failed", f"Error: {error_msg}")
        
        # Cleanup partial download
        if os.path.exists(target_path):
            try:
                shutil.rmtree(target_path)
            except Exception:
                pass
        
        # Retry if retries remaining
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        raise


@celery_app.task(
    bind=True,
    name="app.worker.tasks.download_model.download_ollama_model",
    acks_late=True,
    max_retries=2,
    soft_time_limit=3600,  # 1 hour
    time_limit=3900
)
def download_ollama_model(self, model_db_id: int, model_name: str, target_path: str):
    """
    Pull a model from Ollama.
    
    Args:
        model_db_id: Database ID of the LocalModel
        model_name: Ollama model name (e.g., 'llama3', 'mistral')
        target_path: Local path (for reference, Ollama manages its own storage)
    """
    try:
        import subprocess
        import requests
        
        update_model_status_sync(model_db_id, ModelStatus.DOWNLOADING, 0.0)
        send_progress_update(model_db_id, 0.0, "downloading", f"Pulling {model_name}...")
        
        # Check if Ollama is running
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            response.raise_for_status()
        except Exception:
            raise Exception("Ollama is not running. Please start Ollama first.")
        
        # Pull the model using Ollama library
        client = ollama.Client(host="http://localhost:11434")
        
        try:
            current_digest = ""
            for progress in client.pull(model_name, stream=True):
                status = progress.get("status", "")
                
                # Update status
                if "pulling" in status.lower() and progress.get("total"):
                    total = progress.get("total", 0)
                    completed = progress.get("completed", 0)
                    
                    if total > 0:
                        percent = (completed / total) * 100
                        update_model_status_sync(model_db_id, ModelStatus.DOWNLOADING, percent)
                        
                        # Only send update every 1% or so to avoid flooding
                        send_progress_update(
                            model_db_id, 
                            percent, 
                            "downloading",
                            f"{status}: {completed / (1024**3):.2f} / {total / (1024**3):.2f} GB"
                        )
                
                elif status == "success":
                    break
                    
        except ollama.ResponseError as e:
            raise Exception(f"Ollama API Error: {str(e)}")
        except Exception as e:
             raise Exception(f"Ollama Connection Error: {str(e)}")
        
        # Get model info after pull
        show_response = requests.post(
            "http://localhost:11434/api/show",
            json={"name": model_name},
            timeout=30
        )
        
        if show_response.ok:
            model_info = show_response.json()
            size = model_info.get("size", 0)
        else:
            size = 0
        
        # Update as complete
        # Ollama stores models in its own directory, but we track the model name
        update_model_status_sync(
            model_db_id, 
            ModelStatus.READY, 
            100.0,
            size_bytes=size
        )
        send_progress_update(model_db_id, 100.0, "ready", "Model pulled successfully!")
        
        return {
            "status": "success",
            "model_id": model_db_id,
            "model_name": model_name,
            "size_bytes": size
        }
        
    except SoftTimeLimitExceeded:
        update_model_status_sync(
            model_db_id, 
            ModelStatus.FAILED, 
            error_message="Pull timed out after 1 hour"
        )
        send_progress_update(model_db_id, 0, "failed", "Pull timed out")
        raise Ignore()
        
    except Exception as e:
        error_msg = str(e)
        update_model_status_sync(
            model_db_id, 
            ModelStatus.FAILED, 
            error_message=error_msg
        )
        send_progress_update(model_db_id, 0, "failed", f"Error: {error_msg}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        raise


@celery_app.task(
    name="app.worker.tasks.download_model.check_disk_space"
)
def check_disk_space(required_bytes: int) -> dict:
    """
    Check if there's enough disk space for a download.
    
    Args:
        required_bytes: Required space in bytes
        
    Returns:
        Dict with available space and whether download can proceed
    """
    try:
        base_path = MODELS_BASE_PATH if os.path.exists(MODELS_BASE_PATH) else "/"
        stats = shutil.disk_usage(base_path)
        
        # Leave 5GB buffer
        buffer = 5 * (1024 ** 3)
        available = stats.free - buffer
        
        return {
            "available_bytes": stats.free,
            "available_gb": round(stats.free / (1024**3), 2),
            "required_bytes": required_bytes,
            "required_gb": round(required_bytes / (1024**3), 2),
            "can_download": available >= required_bytes,
            "message": (
                "Sufficient disk space" if available >= required_bytes 
                else f"Insufficient disk space. Need {required_bytes / (1024**3):.2f} GB, "
                     f"only {available / (1024**3):.2f} GB available"
            )
        }
    except Exception as e:
        return {
            "error": str(e),
            "can_download": False
        }


@celery_app.task(
    name="app.worker.tasks.download_model.cleanup_failed_downloads"
)
def cleanup_failed_downloads():
    """
    Periodic task to clean up failed download directories.
    """
    db = get_sync_db()
    try:
        failed_models = db.query(LocalModel).filter(
            LocalModel.status.in_([ModelStatus.FAILED, ModelStatus.CANCELLED])
        ).all()
        
        cleaned = 0
        for model in failed_models:
            if model.local_path and os.path.exists(model.local_path):
                try:
                    shutil.rmtree(model.local_path)
                    cleaned += 1
                except Exception:
                    pass
        
        return {"cleaned_directories": cleaned}
    finally:
        db.close()
