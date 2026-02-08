"""
RAG Retriever
=============

Core retrieval logic for fetching relevant context.
"""

from typing import List, Dict, Any, Optional
from app.ai.rag.vectorstore.chroma_store import ChromaVectorStore # Default to Chroma for now
from app.core.config import settings

class Retriever:
    """Retriever engine for RAG."""

    def __init__(self):
        self.vector_store_type = settings.RAG_VECTOR_DB_TYPE
        
        if self.vector_store_type == "pgvector":
            from app.ai.rag.vectorstore.pgvector_store import PGVectorStore
            self.vector_store = PGVectorStore()
        else:
            # Default to Chroma for dev
            from app.ai.rag.vectorstore.chroma_store import ChromaVectorStore
            self.vector_store = ChromaVectorStore()

    async def retrieve(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Retrieve top K relevant chunks for a query.
        Returns a list of content strings.
        """
        results = await self.vector_store.similarity_search(query, k=k, filter=filter)
        return [res["content"] for res in results]

    async def retrieve_with_metadata(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve top K relevant chunks with metadata.
        """
        return await self.vector_store.similarity_search(query, k=k, filter=filter)

# Global instance
_retriever = None

def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
