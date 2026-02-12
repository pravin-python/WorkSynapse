from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from app.models.note.model import SharePermission, NoteVisibility

# =============================================================================
# TAG SCHEMAS
# =============================================================================

class NoteTagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=7)

class NoteTagCreate(NoteTagBase):
    pass

class NoteTagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=7)

class NoteTagResponse(NoteTagBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

# =============================================================================
# FOLDER SCHEMAS
# =============================================================================

class NoteFolderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    color: Optional[str] = Field(None, max_length=7)

class NoteFolderCreate(NoteFolderBase):
    pass

class NoteFolderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, max_length=7)

class NoteFolderResponse(NoteFolderBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# =============================================================================
# SHARE SCHEMAS
# =============================================================================

class NoteShareCreate(BaseModel):
    email: EmailStr
    permission: SharePermission = SharePermission.VIEW

class NoteShareUpdate(BaseModel):
    permission: SharePermission

class NoteShareResponse(BaseModel):
    id: int
    note_id: int
    shared_with_user_id: int
    shared_by_user_id: int
    permission: SharePermission
    created_at: datetime
    
    # We might want to return user details later
    shared_with_email: Optional[str] = None
    shared_by_email: Optional[str] = None

    class Config:
        from_attributes = True

# =============================================================================
# NOTE SCHEMAS
# =============================================================================

class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    folder_id: Optional[int] = None
    visibility: NoteVisibility = NoteVisibility.PRIVATE
    is_starred: bool = False
    is_archived: bool = False
    is_template: bool = False
    template_category: Optional[str] = None

class NoteCreate(NoteBase):
    tag_ids: List[int] = []

class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    folder_id: Optional[int] = None
    visibility: Optional[NoteVisibility] = None
    is_starred: Optional[bool] = None
    is_archived: Optional[bool] = None
    is_template: Optional[bool] = None
    template_category: Optional[str] = None
    tag_ids: Optional[List[int]] = None

class NoteResponse(NoteBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    version: int = 1
    
    folder: Optional[NoteFolderResponse] = None
    tags: List[NoteTagResponse] = []
    shares: List[NoteShareResponse] = []
    
    # Computed fields for frontend convenience
    is_owner: bool = True
    shared_permission: Optional[SharePermission] = None

    class Config:
        from_attributes = True
