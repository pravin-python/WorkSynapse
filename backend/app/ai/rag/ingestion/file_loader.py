"""
File Loader
===========

Handles processing of uploaded files for RAG ingestion.
"""

from typing import List, Dict, Any
# from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class FileLoader:
    """Loader for file processing."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

    def process_text(self, text: str, metadata: Dict[str, Any]) -> List[str]:
        """Split text into chunks."""
        docs = self.text_splitter.create_documents([text], metadatas=[metadata])
        return [doc.page_content for doc in docs]
