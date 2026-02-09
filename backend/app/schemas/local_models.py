"""
Local Models Pydantic Schemas
=============================

Request/Response schemas for local model management.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================
# ENUMS (mirrored from models)
# ============================================

class ModelSourceEnum(str):
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class ModelStatusEnum(str):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    READY = "ready"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelTypeEnum(str):
    TEXT_GENERATION = "text-generation"
    TEXT2TEXT = "text2text-generation"
    CHAT = "chat"
    EMBEDDING = "embedding"
    IMAGE_GENERATION = "image-generation"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"
    OTHER = "other"


# ============================================
# REQUEST SCHEMAS
# ============================================

class LocalModelDownloadRequest(BaseModel):
    """Request to download a model."""
    model_id: str = Field(..., description="HuggingFace model ID or Ollama model name")
    source: str = Field("huggingface", description="Model source: huggingface, ollama, custom")
    model_type: Optional[str] = Field("text-generation", description="Type of model")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "meta-llama/Llama-3.1-8B-Instruct",
                "source": "huggingface",
                "model_type": "text-generation"
            }
        }


class LocalModelCreate(BaseModel):
    """Create a local model entry (manual registration)."""
    name: str
    model_id: str
    source: str = "custom"
    model_type: str = "text-generation"
    description: Optional[str] = None
    local_path: Optional[str] = None
    size_bytes: Optional[int] = None
    default_params: Optional[dict] = None


class LocalModelUpdate(BaseModel):
    """Update a local model."""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    default_params: Optional[dict] = None


class HuggingFaceSearchRequest(BaseModel):
    """Search HuggingFace models."""
    query: str = Field(..., min_length=2, max_length=200)
    task: Optional[str] = Field(None, description="Filter by task type")
    limit: int = Field(20, ge=1, le=100)


class OllamaModelRequest(BaseModel):
    """Request Ollama model operations."""
    model_name: str = Field(..., description="Ollama model name (e.g., llama3, mistral)")


# ============================================
# RESPONSE SCHEMAS
# ============================================

class LocalModelResponse(BaseModel):
    """Response for a local model."""
    id: int
    name: str
    model_id: str
    source: str
    model_type: str
    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    license: Optional[str] = None
    tags: Optional[List[str]] = None
    
    local_path: Optional[str] = None
    size_bytes: Optional[int] = None
    size_mb: Optional[float] = None
    size_gb: Optional[float] = None
    
    status: str
    progress: float = 0.0
    error_message: Optional[str] = None
    
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    
    download_started_at: Optional[datetime] = None
    download_completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LocalModelListResponse(BaseModel):
    """List of local models."""
    models: List[LocalModelResponse]
    total: int
    downloading_count: int
    ready_count: int


class HuggingFaceModelInfo(BaseModel):
    """HuggingFace model info from API."""
    id: str
    modelId: str
    author: Optional[str] = None
    sha: Optional[str] = None
    lastModified: Optional[str] = None
    private: bool = False
    pipeline_tag: Optional[str] = None
    tags: Optional[List[str]] = None
    downloads: Optional[int] = None
    likes: Optional[int] = None
    library_name: Optional[str] = None
    
    # Computed fields
    size_estimate: Optional[str] = None
    is_downloaded: bool = False


class HuggingFaceSearchResponse(BaseModel):
    """Response for HuggingFace search."""
    models: List[HuggingFaceModelInfo]
    total: int
    query: str


class OllamaModelInfo(BaseModel):
    """Ollama model info."""
    name: str
    model: str
    size: Optional[int] = None
    digest: Optional[str] = None
    modified_at: Optional[str] = None
    is_downloaded: bool = False


class OllamaListResponse(BaseModel):
    """Response for Ollama models list."""
    models: List[OllamaModelInfo]
    total: int


class DownloadProgressResponse(BaseModel):
    """Real-time download progress."""
    model_id: int
    model_name: str
    status: str
    progress: float
    bytes_downloaded: Optional[int] = None
    total_bytes: Optional[int] = None
    speed_mbps: Optional[float] = None
    eta_seconds: Optional[int] = None
    message: Optional[str] = None


class DownloadStartResponse(BaseModel):
    """Response when download is initiated."""
    model_id: int
    task_id: str
    message: str
    websocket_url: str


class ModelStatsResponse(BaseModel):
    """Statistics about local models."""
    total_models: int
    ready_models: int
    downloading_models: int
    failed_models: int
    total_size_gb: float
    disk_free_gb: float
    disk_used_percent: float


# ============================================
# AGENT INTEGRATION SCHEMAS
# ============================================

class AvailableModelForAgent(BaseModel):
    """Model available for agent binding."""
    id: int
    name: str
    model_id: str
    source: str
    model_type: str
    size_gb: Optional[float] = None
    is_local: bool = True


class AgentModelBinding(BaseModel):
    """Bind a local model to an agent."""
    model_type: str = Field("local", description="'local' or 'api'")
    local_model_id: Optional[int] = Field(None, description="ID of local model if type is 'local'")
    api_provider: Optional[str] = Field(None, description="Provider name if type is 'api'")
    api_model_name: Optional[str] = Field(None, description="Model name if type is 'api'")


class ChatRequest(BaseModel):
    """Request for chat with local model."""
    model_id: int
    messages: List[dict] = Field(..., description="List of messages: [{'role': 'user', 'content': 'hello'}]")
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Response from chat with local model."""
    response: str
    model: str
    created_at: str
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
