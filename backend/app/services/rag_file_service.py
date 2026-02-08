
import os
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import List
from app.core.config import settings

class RagFileService:
    """
    Service to handle RAG file storage and management.
    Documents are stored in media/rag_files/{agent_id}/{filename}
    """
    
    BASE_DIR = Path("media/rag_files")
    
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md', '.csv'}
    
    @classmethod
    def _get_agent_dir(cls, agent_id: int) -> Path:
        agent_dir = cls.BASE_DIR / str(agent_id)
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir

    @classmethod
    def validate_file(cls, file: UploadFile):
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {ext} not supported. Allowed: {cls.ALLOWED_EXTENSIONS}"
            )
        # 10MB limit
        # Note: checking size on stream is tricky without reading it entirely, 
        # but typically handled by nginx or framework limits. 
        # We'll assume basic validation here.

    @classmethod
    async def save_file(cls, agent_id: int, file: UploadFile) -> str:
        """
        Saves uploaded file to disk and returns the relative path.
        """
        cls.validate_file(file)
        agent_dir = cls._get_agent_dir(agent_id)
        
        # Sanitize filename (basic)
        filename = os.path.basename(file.filename)
        file_path = agent_dir / filename
        
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
            
        return str(file_path)

    @classmethod
    def delete_file(cls, file_path_str: str):
        """
        Deletes a file from disk.
        """
        path = Path(file_path_str)
        if path.exists():
            try:
                os.remove(path)
            except Exception as e:
                # Log error but don't crash
                print(f"Error deleting file {path}: {e}")
