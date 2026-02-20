"""
ChromaDB Vector Store
=====================

Local vector store implementation using ChromaDB.
"""

import chromadb
from typing import List, Dict, Any, Optional
from app.agents.rag.vectorstore.base import VectorStore
from app.agents.rag.embedding_service import get_embedding_service
from app.core.config import settings

class ChromaVectorStore(VectorStore):
    """ChromaDB implementation of VectorStore."""

    def __init__(self, collection_name: str = "worksynapse_knowledge"):
        self.client = chromadb.Client() # or HttpClient for server mode
        self.embedding_service = get_embedding_service()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_service # Chroma handles embedding if passed, or we embed manually
        )

    def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add texts to Chroma collection."""
        # Note: If embedding_function is set in collection, we just pass texts.
        # If we use our own embedding service manually, we'd generate embeddings here.
        # For simplicity with Chroma's interface, we let Chroma use our embedding function wrapper 
        # OR we generate raw embeddings. 
        # Let's generate raw embeddings to be explicit and provider-agnostic.
        
        embeddings = self.embedding_service.embed_documents(texts)
        if not ids:
            import uuid
            ids = [str(uuid.uuid4()) for _ in texts]
            
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        return ids

    def similarity_search(
        self, 
        query: str, 
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search in Chroma collection."""
        query_embedding = self.embedding_service.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter
        )
        
        # Format results
        output = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                output.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0.0
                })
        return output

    def delete(self, ids: List[str]) -> bool:
        """Delete chunks from Chroma."""
        self.collection.delete(ids=ids)
        return True
