"""
PGVector Store
==============

Production-grade vector store using PostgreSQL with pgvector extension.
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_postgres import PGVector
from langchain_core.documents import Document

from app.core.config import settings
from app.agents.rag.embedding_service import get_embedding_service
from app.agents.rag.vectorstore.base import VectorStore

logger = logging.getLogger(__name__)

class PGVectorStore(VectorStore):
    """PGVector implementation using LangChain integration."""

    def __init__(self, collection_name: str = "worksynapse_knowledge"):
        self.embedding_service = get_embedding_service()
        
        # Use sync embedding client for PGVector initialization as it requires it
        # But we will use it in async mostly regarding app flow
        
        # Connection string
        connection_string = settings.PGVECTOR_CONNECTION_URI or settings.DATABASE_URL
        if connection_string.startswith("postgresql+asyncpg"):
             # LangChain PGVector uses psycopg2/3 usually, check driver compatibility
             # For now assume we might need a sync driver string
             connection_string = connection_string.replace("+asyncpg", "")

        try:
            self.store = PGVector(
                embeddings=self.embedding_service._client,
                collection_name=collection_name,
                connection=connection_string,
                use_jsonb=True,
            )
        except Exception as e:
            logger.error(f"Failed to initialize PGVector: {e}")
            raise

    async def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]) -> None:
        """Add documents to PGVector."""
        docs = [
            Document(page_content=txt, metadata=meta) 
            for txt, meta in zip(documents, metadatas)
        ]
        # PGVector supports aadd_documents (async)
        await self.store.aadd_documents(docs, ids=ids)

    async def similarity_search(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search similar documents."""
        # Note: LangChain PGVector filter format might need specific attention
        results = await self.store.asimilarity_search_with_score(query, k=k, filter=filter)
        
        # Parse results: List of (Document, float)
        output = []
        for doc, score in results:
            output.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score,
                "id": doc.metadata.get("id") # Assuming we stored ID in metadata or it's handled
            })
        return output

    async def delete_documents(self, ids: List[str]) -> None:
        """Delete documents."""
        await self.store.adelete(ids=ids)
