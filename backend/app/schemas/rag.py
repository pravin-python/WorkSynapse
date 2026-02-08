
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RagDocumentBase(BaseModel):
    filename: str
    file_type: str
    file_size: int

class RagDocumentResponse(RagDocumentBase):
    id: int
    created_at: datetime
    uploaded_by_id: Optional[int] = None

    class Config:
        from_attributes = True
