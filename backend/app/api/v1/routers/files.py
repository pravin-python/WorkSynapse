"""
Secure File Upload Router
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import os
import hashlib
import time

from app.api.deps import get_current_user
from app.models.user.model import User
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "text/plain", "text/csv",
    "application/json",
    "application/zip",
}


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate file type and size."""
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        return False, f"File type {file.content_type} not allowed"
    
    return True, ""


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a file with validation."""
    # Validate
    is_valid, error = validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    # Read file content
    content = await file.read()
    
    # Check size from config
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB}MB)")
    
    # Generate unique filename
    file_hash = hashlib.md5(content).hexdigest()[:12]
    timestamp = int(time.time())
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    safe_filename = f"{current_user.id}_{timestamp}_{file_hash}{ext}"
    
    # Save file using path from config
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, safe_filename)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    logger.info(f"File uploaded: {safe_filename} by user {current_user.id}")
    
    return {
        "filename": safe_filename,
        "size": len(content),
        "content_type": file.content_type
    }


@router.get("/{filename}")
async def get_file(filename: str, current_user: User = Depends(get_current_user)):
    """Get file info."""
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "filename": filename,
        "size": os.path.getsize(file_path)
    }
