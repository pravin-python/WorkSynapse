
import os
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.models import User
from app.models.rag import RagDocument, AgentRagDocument
from app.models.agent_builder.model import CustomAgent
from app.services.rag_file_service import RagFileService
from app.worker.tasks.rag import process_rag_document

router = APIRouter()

@router.post("/upload", response_model=Any)
async def upload_rag_document(
    agent_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a document for RAG processing.
    1. Validate & Save file
    2. Create DB record
    3. Link to Agent
    4. Trigger async processing
    """
    # Verify agent exists and belongs to user (or public/shared logic)
    agent = db.query(CustomAgent).filter(CustomAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check permissions (simplified)
    # if agent.created_by_user_id != current_user.id: ...

    try:
        # 1. Save File
        file_path = await RagFileService.save_file(agent_id, file)
        
        # Get file size
        file_size = 0
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)

        # 2. Create DB Record
        rag_doc = RagDocument(
            filename=file.filename,
            file_path=file_path,
            file_type=file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown',
            file_size=file_size,
            uploaded_by_id=current_user.id
        )
        db.add(rag_doc)
        db.flush() # Get ID
        
        # 3. Link to Agent
        link = AgentRagDocument(
            agent_id=agent.id,
            document_id=rag_doc.id
        )
        db.add(link)
        db.commit()
        db.refresh(rag_doc)
        
        # 4. Trigger Async Processing
        process_rag_document.delay(rag_doc.id)
        
        return {
            "id": rag_doc.id,
            "filename": rag_doc.filename,
            "status": "processing" # TODO: Add status field to model if needed, or infer from chunks existence
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        # Clean up file if created
        # RagFileService.delete_file(...)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}/documents", response_model=List[Any])
def get_agent_documents(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List documents attached to an agent.
    """
    agent = db.query(CustomAgent).filter(CustomAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    docs = (
        db.query(RagDocument)
        .join(AgentRagDocument, AgentRagDocument.document_id == RagDocument.id)
        .filter(AgentRagDocument.agent_id == agent_id)
        .all()
    )
    
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "created_at": d.created_at,
            # "status": "ready" if d.chunks else "processing"
        }
        for d in docs
    ]

@router.delete("/documents/{document_id}")
def delete_rag_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a document and its chunks.
    """
    doc = db.query(RagDocument).filter(RagDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Check permissions
    if doc.uploaded_by_id != current_user.id:
        # Allow if admin or agent owner...
        pass

    # Delete file from disk
    RagFileService.delete_file(doc.file_path)
    
    # DB cascade delete handles chunks and links
    db.delete(doc)
    db.commit()
    
    return {"message": "Document deleted"}
