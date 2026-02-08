"""
RAG Knowledge Models
====================

Database models for storing RAG documents and chunks.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import Base, AuditMixin
from typing import Optional, List

class RagDocument(Base, AuditMixin):
    """
    Stores uploaded files for RAG.
    """
    __tablename__ = "rag_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, docx, txt
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    
    uploaded_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # chunks relationship
    chunks: Mapped[List["RagChunk"]] = relationship(
        "RagChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    # agent links
    agent_links: Mapped[List["AgentRagDocument"]] = relationship(
        "AgentRagDocument",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<RagDocument {self.filename}>"


class AgentRagDocument(Base, AuditMixin):
    """
    Link between an Agent and a RagDocument.
    """
    __tablename__ = "agent_rag_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("custom_agents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    document: Mapped["RagDocument"] = relationship("RagDocument", back_populates="agent_links")
    agent: Mapped["CustomAgent"] = relationship("CustomAgent", back_populates="rag_documents")

    def __repr__(self):
        return f"<AgentRagDocument Agent={self.agent_id} Doc={self.document_id}>"


class RagChunk(Base, AuditMixin):
    """
    Stores chunked content for a document.
    """
    __tablename__ = "rag_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    document_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("rag_documents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Renamed to avoid conflicts, mapped to 'metadata' in logic if needed

    # Relationships
    document: Mapped["RagDocument"] = relationship("RagDocument", back_populates="chunks")

    def __repr__(self):
        return f"<RagChunk {self.id} from Doc {self.document_id}>"
