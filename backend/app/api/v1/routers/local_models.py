"""
Local Models API Router
=======================

API endpoints for local model management, downloads, and search.
"""

import os
import json
import httpx
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user.model import User
from app.models.local_models.model import LocalModel, ModelSource, ModelStatus, ModelType
from app.schemas.local_models import (
    LocalModelDownloadRequest, LocalModelCreate, LocalModelUpdate,
    LocalModelResponse, LocalModelListResponse,
    HuggingFaceSearchRequest, HuggingFaceSearchResponse, HuggingFaceModelInfo,
    OllamaListResponse, OllamaModelInfo,
    DownloadStartResponse, DownloadProgressResponse, ModelStatsResponse,
    AvailableModelForAgent, ChatRequest, ChatResponse
)
from app.services.local_model_service import LocalModelService, LocalModelServiceError
import ollama


router = APIRouter()


# ============================================
# HELPER FUNCTIONS
# ============================================

def model_to_response(model: LocalModel) -> LocalModelResponse:
    """Convert LocalModel to response schema."""
    tags = None
    if model.tags:
        try:
            tags = json.loads(model.tags)
        except json.JSONDecodeError:
            tags = None
    
    return LocalModelResponse(
        id=model.id,
        name=model.name,
        model_id=model.model_id,
        source=model.source.value,
        model_type=model.model_type.value,
        description=model.description,
        author=model.author,
        version=model.version,
        license=model.license,
        tags=tags,
        local_path=model.local_path,
        size_bytes=model.size_bytes,
        size_mb=model.size_mb,
        size_gb=model.size_gb,
        status=model.status.value,
        progress=model.progress,
        error_message=model.error_message,
        is_active=model.is_active,
        last_used_at=model.last_used_at,
        usage_count=model.usage_count,
        download_started_at=model.download_started_at,
        download_completed_at=model.download_completed_at,
        created_at=model.created_at
    )


def require_admin_or_staff(user: User):
    """Check if user has admin or staff role."""
    allowed_roles = ["ADMIN", "SUPER_ADMIN", "STAFF", "Admin", "SuperUser"]
    if user.role.value not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Staff access required"
        )


# ============================================
# MODEL CRUD ENDPOINTS
# ============================================

@router.get("", response_model=LocalModelListResponse)
async def list_local_models(
    source: Optional[str] = Query(None, description="Filter by source"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    ready_only: bool = Query(False, description="Only show ready models"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all local models."""
    source_enum = ModelSource(source) if source else None
    status_enum = ModelStatus(status_filter) if status_filter else None
    
    models, total = await LocalModelService.get_models(
        db, 
        source=source_enum,
        status=status_enum,
        ready_only=ready_only,
        limit=limit,
        offset=offset
    )
    
    # Count by status
    downloading = sum(1 for m in models if m.status == ModelStatus.DOWNLOADING)
    ready = sum(1 for m in models if m.status == ModelStatus.READY)
    
    return LocalModelListResponse(
        models=[model_to_response(m) for m in models],
        total=total,
        downloading_count=downloading,
        ready_count=ready
    )


@router.get("/stats", response_model=ModelStatsResponse)
async def get_model_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get model statistics."""
    stats = await LocalModelService.get_stats(db)
    return ModelStatsResponse(**stats)





@router.post("", response_model=LocalModelResponse, status_code=status.HTTP_201_CREATED)
async def create_local_model(
    data: LocalModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually register a local model."""
    require_admin_or_staff(current_user)
    
    try:
        model = await LocalModelService.create_model(db, data, current_user.id)
        return model_to_response(model)
    except LocalModelServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))








# ============================================
# DOWNLOAD ENDPOINTS
# ============================================

@router.post("/download", response_model=DownloadStartResponse)
async def start_model_download(
    data: LocalModelDownloadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start downloading a model.
    
    This initiates a background Celery task for the download.
    Connect to the WebSocket endpoint for real-time progress.
    """
    require_admin_or_staff(current_user)
    
    try:
        # Parse enums
        source = ModelSource(data.source)
        model_type = ModelType(data.model_type) if data.model_type else ModelType.TEXT_GENERATION
        
        # Create model entry
        model = await LocalModelService.initiate_download(
            db,
            model_id=data.model_id,
            source=source,
            model_type=model_type,
            user_id=current_user.id
        )
        
        # Start appropriate Celery task
        if source == ModelSource.HUGGINGFACE:
            from app.worker.tasks.download_model import download_huggingface_model
            task = download_huggingface_model.delay(
                model.id, 
                data.model_id, 
                model.local_path
            )
        elif source == ModelSource.OLLAMA:
            from app.worker.tasks.download_model import download_ollama_model
            task = download_ollama_model.delay(
                model.id,
                data.model_id,
                model.local_path
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Custom models must be manually registered"
            )
        
        # Update model with task ID
        model.task_id = task.id
        model.status = ModelStatus.DOWNLOADING
        await db.commit()
        
        return DownloadStartResponse(
            model_id=model.id,
            task_id=task.id,
            message=f"Download started for {data.model_id}",
            websocket_url=f"/ws/model-download/{model.id}"
        )
        
    except LocalModelServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{model_id}/cancel")
async def cancel_model_download(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an ongoing download."""
    require_admin_or_staff(current_user)
    
    try:
        success = await LocalModelService.cancel_download(db, model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model not found")
        return {"message": "Download cancelled successfully"}
    except LocalModelServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{model_id}/progress", response_model=DownloadProgressResponse)
async def get_download_progress(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current download progress."""
    model = await LocalModelService.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return DownloadProgressResponse(
        model_id=model.id,
        model_name=model.name,
        status=model.status.value,
        progress=model.progress,
        bytes_downloaded=None,  # Could be tracked in future
        total_bytes=model.size_bytes,
        message=model.error_message if model.status == ModelStatus.FAILED else None
    )


# ============================================
# HUGGINGFACE SEARCH
# ============================================

@router.post("/search/huggingface", response_model=HuggingFaceSearchResponse)
async def search_huggingface_models(
    data: HuggingFaceSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for models on HuggingFace Hub."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "search": data.query,
                "limit": data.limit,
                "sort": "downloads",
                "direction": "-1"
            }
            
            if data.task:
                params["pipeline_tag"] = data.task
            
            response = await client.get(
                "https://huggingface.co/api/models",
                params=params
            )
            response.raise_for_status()
            
            models_data = response.json()
            
            # Get list of already downloaded model IDs
            downloaded_models, _ = await LocalModelService.get_models(
                db, source=ModelSource.HUGGINGFACE
            )
            downloaded_ids = {m.model_id for m in downloaded_models}
            
            models = []
            for m in models_data:
                model_info = HuggingFaceModelInfo(
                    id=m.get("id", ""),
                    modelId=m.get("modelId", m.get("id", "")),
                    author=m.get("author"),
                    sha=m.get("sha"),
                    lastModified=m.get("lastModified"),
                    private=m.get("private", False),
                    pipeline_tag=m.get("pipeline_tag"),
                    tags=m.get("tags", []),
                    downloads=m.get("downloads"),
                    likes=m.get("likes"),
                    library_name=m.get("library_name"),
                    is_downloaded=m.get("id", "") in downloaded_ids
                )
                models.append(model_info)
            
            return HuggingFaceSearchResponse(
                models=models,
                total=len(models),
                query=data.query
            )
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to search HuggingFace: {str(e)}"
        )


# ============================================
# CHAT / INFERENCE
# ============================================

@router.post("/chat", response_model=ChatResponse)
async def chat_with_model(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Chat with a local model using Ollama library."""
    # Get model to verify it exists and get its name
    model = await LocalModelService.get_model(db, request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
        
    if model.source != ModelSource.OLLAMA:
        raise HTTPException(status_code=400, detail="Only Ollama models are supported for direct chat")

    try:
        from fastapi.concurrency import run_in_threadpool
        
        # Options for generation
        options = {
            "temperature": request.temperature,
        }
        if request.max_tokens:
            options["num_predict"] = request.max_tokens

        # Use ollama library in threadpool to avoid blocking
        response = await run_in_threadpool(
            ollama.chat,
            model=model.name,
            messages=request.messages,
            options=options,
            stream=False
        )
        
        # Record usage
        await LocalModelService.record_model_usage(db, model.id)
        
        return ChatResponse(
            response=response["message"]["content"],
            model=response["model"],
            created_at=str(response["created_at"]),
            done=response["done"],
            total_duration=response.get("total_duration"),
            load_duration=response.get("load_duration"),
            prompt_eval_count=response.get("prompt_eval_count"),
            eval_count=response.get("eval_count")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama Error: {str(e)}")


# ============================================
# OLLAMA INTEGRATION
# ============================================

@router.get("/ollama/available", response_model=OllamaListResponse)
async def list_available_ollama_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List models available in Ollama library."""
    # Popular Ollama models
    popular_models = [
        {"name": "llama3.1", "model": "llama3.1:latest", "size": 4700000000},
        {"name": "llama3", "model": "llama3:latest", "size": 4700000000},
        {"name": "mistral", "model": "mistral:latest", "size": 4100000000},
        {"name": "codellama", "model": "codellama:latest", "size": 3800000000},
        {"name": "phi3", "model": "phi3:latest", "size": 2300000000},
        {"name": "gemma2", "model": "gemma2:latest", "size": 5400000000},
        {"name": "qwen2", "model": "qwen2:latest", "size": 4400000000},
        {"name": "llava", "model": "llava:latest", "size": 4500000000},
        {"name": "deepseek-coder", "model": "deepseek-coder:latest", "size": 800000000},
        {"name": "neural-chat", "model": "neural-chat:latest", "size": 4100000000},
    ]
    
    # Get already downloaded models
    downloaded, _ = await LocalModelService.get_models(db, source=ModelSource.OLLAMA)
    downloaded_names = {m.model_id for m in downloaded}
    
    models = [
        OllamaModelInfo(
            name=m["name"],
            model=m["model"],
            size=m["size"],
            is_downloaded=m["name"] in downloaded_names
        )
        for m in popular_models
    ]
    
    return OllamaListResponse(models=models, total=len(models))


@router.get("/ollama/local", response_model=OllamaListResponse)
async def list_local_ollama_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List models currently installed in local Ollama instance."""
    try:
        from fastapi.concurrency import run_in_threadpool
        # Use ollama library
        response = await run_in_threadpool(ollama.list)
        
        models = []
        for m in response.get("models", []):
            models.append(OllamaModelInfo(
                name=m.get("name", ""),
                model=m.get("model", m.get("name", "")),
                size=m.get("size"),
                digest=m.get("digest"),
                modified_at=str(m.get("modified_at")) if m.get("modified_at") else None,
                is_downloaded=True
            ))
        
        return OllamaListResponse(models=models, total=len(models))
            
    except Exception:
        # Ollama not running
        return OllamaListResponse(models=[], total=0)
            



# ============================================
# AGENT INTEGRATION
# ============================================

@router.get("/for-agent", response_model=List[AvailableModelForAgent])
async def get_models_for_agent(
    source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get local models available for agent binding."""
    source_enum = ModelSource(source) if source else None
    
    models = await LocalModelService.get_models_for_agent(db, source=source_enum)
    
    return [
        AvailableModelForAgent(
            id=m.id,
            name=m.name,
            model_id=m.model_id,
            source=m.source.value,
            model_type=m.model_type.value,
            size_gb=m.size_gb,
            is_local=True
        )
        for m in models
    ]


@router.get("/{model_id}", response_model=LocalModelResponse)
async def get_local_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific local model."""
    from app.services.local_model_service import LocalModelService
    model = await LocalModelService.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model_to_response(model)


@router.patch("/{model_id}", response_model=LocalModelResponse)
async def update_local_model(
    model_id: int,
    data: LocalModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a local model."""
    require_admin_or_staff(current_user)
    
    from app.services.local_model_service import LocalModelService
    model = await LocalModelService.update_model(db, model_id, data)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model_to_response(model)


@router.delete("/{model_id}")
async def delete_local_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a local model and its files."""
    require_admin_or_staff(current_user)
    
    from app.services.local_model_service import LocalModelService
    try:
        success = await LocalModelService.delete_model(db, model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model not found")
        return {"message": "Model deleted successfully"}
    except LocalModelServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
