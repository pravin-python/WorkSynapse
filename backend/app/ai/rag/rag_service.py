"""
RAG Service
===========

High-level service API for RAG operations: retrieval and optional synchronous ingestion (if needed).
Most ingestion happens asynchronously via Celery.
"""

from typing import List, Optional, Dict, Any
from app.ai.rag.retriever import get_retriever
# from app.models.rag import RagDocument 

class RAGService:
    """Service layer for RAG operations."""

    def __init__(self):
        self.retriever = get_retriever()

    async def retrieve_context(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Retrieve context text chunks for a given user query.
        This is used by the Agent Orchestrator.
        """
        return await self.retriever.retrieve(query, k=k, filter=filter)

    async def retrieve_with_metadata(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve context with metadata.
        """
        return await self.retriever.retrieve_with_metadata(query, k=k, filter=filter)

    # Note: Ingestion is now handled by app.worker.tasks.rag.process_rag_document

# Global instance
_rag_service = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
