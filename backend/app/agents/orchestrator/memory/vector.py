"""
Vector Memory
=============

Long-term vector-based memory for agents using embeddings.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MemoryDocument(BaseModel):
    """A document stored in vector memory."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VectorMemory:
    """
    Vector memory for agents.

    Provides long-term semantic memory using vector embeddings.
    Supports Chroma, Redis, or in-memory storage.
    """

    def __init__(
        self,
        agent_id: int,
        collection_name: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
        k_results: int = 5,
    ):
        """
        Initialize vector memory.

        Args:
            agent_id: ID of the agent this memory belongs to
            collection_name: Optional custom collection name
            embedding_model: Embedding model to use
            k_results: Default number of results to return
        """
        self.agent_id = agent_id
        self.collection_name = collection_name or f"agent_{agent_id}_memory"
        self.embedding_model = embedding_model
        self.k_results = k_results
        self._vectorstore = None
        self._embeddings = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the vector store and embeddings."""
        if self._initialized:
            return

        try:
            # Import LangChain components
            from langchain_openai import OpenAIEmbeddings
            from langchain_chroma import Chroma

            from app.agents.orchestrator.config import get_orchestrator_config

            config = get_orchestrator_config()

            # Initialize embeddings
            if config.openai_api_key:
                self._embeddings = OpenAIEmbeddings(
                    api_key=config.openai_api_key,
                    model=self.embedding_model,
                )
            else:
                # Use a fallback or mock embeddings
                logger.warning("No OpenAI API key for embeddings, using mock")
                self._embeddings = None

            # Initialize vector store
            if self._embeddings:
                self._vectorstore = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self._embeddings,
                    persist_directory=config.chroma_persist_directory,
                )

            self._initialized = True
            logger.info(f"Vector memory initialized for agent {self.agent_id}")

        except Exception as e:
            logger.error(f"Failed to initialize vector memory: {e}")
            raise

    async def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a document to vector memory.

        Args:
            content: Document content
            metadata: Optional document metadata

        Returns:
            Document ID
        """
        if not self._initialized:
            await self.initialize()

        doc_id = str(uuid.uuid4())
        metadata = metadata or {}
        metadata["agent_id"] = self.agent_id
        metadata["created_at"] = datetime.utcnow().isoformat()

        if self._vectorstore:
            self._vectorstore.add_texts(
                texts=[content],
                metadatas=[metadata],
                ids=[doc_id],
            )
        else:
            logger.warning("Vector store not available, document not persisted")

        return doc_id

    async def add_batch(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Add multiple documents to vector memory.

        Args:
            documents: List of dicts with 'content' and optional 'metadata'

        Returns:
            List of document IDs
        """
        if not self._initialized:
            await self.initialize()

        doc_ids = []
        texts = []
        metadatas = []

        for doc in documents:
            doc_id = str(uuid.uuid4())
            doc_ids.append(doc_id)
            texts.append(doc["content"])

            metadata = doc.get("metadata", {})
            metadata["agent_id"] = self.agent_id
            metadata["created_at"] = datetime.utcnow().isoformat()
            metadatas.append(metadata)

        if self._vectorstore:
            self._vectorstore.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=doc_ids,
            )

        return doc_ids

    async def search(
        self,
        query: str,
        k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query: Search query
            k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of matching documents with scores
        """
        if not self._initialized:
            await self.initialize()

        k = k or self.k_results

        if not self._vectorstore:
            logger.warning("Vector store not available")
            return []

        # Build filter
        where_filter = {"agent_id": self.agent_id}
        if filter_metadata:
            where_filter.update(filter_metadata)

        try:
            results = self._vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=where_filter,
            )

            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score,
                }
                for doc, score in results
            ]

        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    async def delete(self, doc_ids: List[str]) -> None:
        """
        Delete documents by ID.

        Args:
            doc_ids: List of document IDs to delete
        """
        if not self._initialized:
            await self.initialize()

        if self._vectorstore:
            self._vectorstore.delete(ids=doc_ids)

    async def clear(self) -> None:
        """Clear all documents for this agent."""
        if not self._initialized:
            await self.initialize()

        if self._vectorstore:
            # Delete entire collection
            try:
                self._vectorstore.delete_collection()
                self._initialized = False
            except Exception as e:
                logger.error(f"Failed to clear vector memory: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self._initialized:
            await self.initialize()

        stats = {
            "agent_id": self.agent_id,
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model,
            "initialized": self._initialized,
        }

        if self._vectorstore:
            # Try to get collection count
            try:
                collection = self._vectorstore._collection
                stats["document_count"] = collection.count()
            except Exception:
                stats["document_count"] = "unknown"

        return stats

    def get_retriever(self, k: Optional[int] = None):
        """
        Get a LangChain retriever for this memory.

        Args:
            k: Number of documents to retrieve

        Returns:
            LangChain retriever
        """
        if not self._vectorstore:
            return None

        return self._vectorstore.as_retriever(
            search_kwargs={
                "k": k or self.k_results,
                "filter": {"agent_id": self.agent_id},
            }
        )
