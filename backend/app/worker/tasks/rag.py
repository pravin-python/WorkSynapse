
import os
from celery import shared_task
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.rag import RagDocument, RagChunk
from app.ai.rag.embeddings.embedding_service import EmbeddingService
from app.ai.rag.vectorstore.pgvector_store import PGVectorStore
from app.core.config import settings

# Text Extraction (Simple implementation for now)
import PyPDF2

# ... imports
import asyncio
from typing import List

# ...

@shared_task(name="app.worker.tasks.rag.process_rag_document")
def process_rag_document(document_id: int):
    """
    Background task to process a RAG document:
    1. Read file
    2. Extract text
    3. Chunk text
    4. Save to DB & Vector Store
    """
    from app.database.session import SessionLocal
    db = SessionLocal()
    
    try:
        doc = db.query(RagDocument).filter(RagDocument.id == document_id).first()
        if not doc:
            print(f"Document {document_id} not found.")
            return

        file_path = doc.file_path
        if not os.path.exists(file_path):
            print(f"File {file_path} not found.")
            return

        # 1. Extract Text
        text_content = ""
        try:
            if doc.file_type == '.pdf':
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text_content += extracted + "\n"
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content = f.read()
        except Exception as e:
            print(f"Failed to read file: {e}")
            return

        if not text_content.strip():
            print(f"No text extracted from {doc.filename}")
            return

        # 2. Chunk Text (Simple fixed-size chunking for now)
        # TODO: Reuse FileLoader or LangChain splitter for consistency
        chunk_size = 1000
        overlap = 200
        chunks = []
        for i in range(0, len(text_content), chunk_size - overlap):
            chunks.append(text_content[i:i + chunk_size])

        if not chunks:
            return

        # 3. Prepare Data
        ids = [f"doc_{doc.id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"document_id": doc.id, "filename": doc.filename, "chunk_index": i} for i in range(len(chunks))]

        # 4. Add to Vector Store (Async wrapper)
        try:
            vector_store = PGVectorStore()
            asyncio.run(vector_store.add_documents(chunks, metadatas, ids))
            print(f"Added {len(chunks)} chunks to Vector Store.")
        except Exception as e:
            print(f"Failed to add to vector store: {e}")
            # Continue to save to SQL as backup? Or fail?
            # For now, we log and continue, but in production we might want to retry.

        # 5. Save chunks to SQL DB
        for i, chunk_text in enumerate(chunks):
            rag_chunk = RagChunk(
                document_id=doc.id,
                content=chunk_text,
                embedding_id=ids[i],
                chunk_index=i,
                metadata_json=metadatas[i]
            )
            db.add(rag_chunk)
        
        db.commit()
        print(f"Processed {len(chunks)} chunks for document {doc.filename} saved to SQL.")

    except Exception as e:
        print(f"Error processing document {document_id}: {str(e)}")
        db.rollback()
    finally:
        db.close()
