"""
Vector Store Base Interface
===========================

Abstract base class for vector store implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStore(ABC):
    """Abstract interface for vector database operations."""

    @abstractmethod
    async def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]) -> None:
        """Add documents to the vector store."""
        pass

    @abstractmethod
    async def similarity_search(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.
        Returns list of dicts with 'content' and 'metadata'.
        """
        pass

    @abstractmethod
    async def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by ID."""
        pass
