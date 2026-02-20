"""
RAG Embedding Service
=====================

Handles the generation of embeddings using various providers.
Supports OpenAI, HuggingFace, and Local embeddings.
"""

from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import settings

class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, provider: str = "openai", model_name: Optional[str] = None):
        """
        Initialize the embedding service.
        
        Args:
            provider: Embedding provider ('openai', 'huggingface', 'local')
            model_name: Specific model name to use
        """
        self.provider = provider
        self.model_name = model_name
        self._client = self._initialize_client()

    def _initialize_client(self):
        """Initialize the underlying embedding client."""
        try:
            if self.provider == "openai":
                if not settings.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY is not set")
                return OpenAIEmbeddings(
                    model=self.model_name or "text-embedding-3-small",
                    api_key=settings.OPENAI_API_KEY
                )
            elif self.provider == "huggingface":
                return HuggingFaceEmbeddings(
                    model_name=self.model_name or "sentence-transformers/all-MiniLM-L6-v2"
                )
            elif self.provider == "local":
                # For local deployment, we can use HuggingFace embeddings running continuously
                return HuggingFaceEmbeddings(
                    model_name=self.model_name or "sentence-transformers/all-MiniLM-L6-v2"
                )
            else:
                raise ValueError(f"Unsupported embedding provider: {self.provider}")
        except Exception as e:
            # Fallback to a safe default if initialization fails (e.g. API key missing)
            # This ensures the service doesn't crash the entire app on startup
            print(f"Embedding initialization failed: {e}. Falling back to dummy embeddings.")
            # In production, you might want to raise here, but for now we'll log it.
            # Returning None or a dummy would be better. 
            # For this implementation, let's re-raise to be strict about config.
            raise

    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text (Async wrapper)."""
        # LangChain embeddings are sync usually, but we expose async for future proofing
        return self._client.embed_query(text)
    
    def embed_query_sync(self, text: str) -> List[float]:
         """Generate embedding for a single query text (Sync)."""
         return self._client.embed_query(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents (Async wrapper)."""
        return self._client.embed_documents(texts)

# Global instance for easy access
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(
            provider=settings.EMBEDDING_PROVIDER,
            model_name=settings.EMBEDDING_MODEL
        )
    return _embedding_service
