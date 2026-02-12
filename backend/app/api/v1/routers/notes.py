"""Notes Router"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models import User
from app.schemas.note import (
    NoteCreate, NoteUpdate, NoteResponse,
    NoteFolderCreate, NoteFolderUpdate, NoteFolderResponse,
    NoteTagCreate, NoteTagUpdate, NoteTagResponse,
    NoteShareCreate, NoteShareResponse
)
from app.services.notes_service import notes_service
from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException

router = APIRouter()

# =============================================================================
# NOTES ENDPOINTS
# =============================================================================

@router.get("/", response_model=List[NoteResponse])
async def read_notes(
    search: Optional[str] = None,
    folder_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    is_starred: Optional[bool] = None,
    # "Shared with me" filter
    shared: Optional[bool] = None, 
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve notes.
    """
    notes, total = await notes_service.get_notes(
        db=db,
        user_id=current_user.id,
        search=search,
        folder_id=folder_id,
        tag_id=tag_id,
        is_starred=is_starred,
        is_shared=shared,
        skip=skip,
        limit=limit
    )
    return notes


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_in: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new note.
    Defaults: visibility=PRIVATE, is_template=false, is_archived=false, is_starred=false
    """
    return await notes_service.create_note(db, note_in, current_user.id)


@router.get("/{id}", response_model=NoteResponse)
async def read_note(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific note by ID.
    """
    return await notes_service.get_note(db, id, current_user.id)


@router.put("/{id}", response_model=NoteResponse)
async def update_note(
    id: int,
    note_in: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a note.
    """
    return await notes_service.update_note(db, id, note_in, current_user.id)


@router.delete("/{id}")
async def delete_note(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a note.
    """
    await notes_service.delete_note(db, id, current_user.id)
    return {"status": "success"}


@router.post("/{id}/star", response_model=NoteResponse)
async def star_note(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Star a note.
    """
    return await notes_service.star_note(db, id, current_user.id, True)


@router.post("/{id}/unstar", response_model=NoteResponse)
async def unstar_note(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Unstar a note.
    """
    return await notes_service.star_note(db, id, current_user.id, False)


# =============================================================================
# FOLDER ENDPOINTS
# =============================================================================

@router.get("/folders/all", response_model=List[NoteFolderResponse])
async def read_folders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all folders for current user.
    """
    return await notes_service.get_folders(db, current_user.id)


@router.post("/folders", response_model=NoteFolderResponse)
async def create_folder(
    folder_in: NoteFolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new folder.
    """
    return await notes_service.create_folder(db, folder_in, current_user.id)


@router.delete("/folders/{id}")
async def delete_folder(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a folder.
    """
    await notes_service.delete_folder(db, id, current_user.id)
    return {"status": "success"}


# =============================================================================
# TAG ENDPOINTS
# =============================================================================

@router.get("/tags/all", response_model=List[NoteTagResponse])
async def read_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all tags for current user.
    """
    return await notes_service.get_tags(db, current_user.id)


@router.post("/tags", response_model=NoteTagResponse)
async def create_tag(
    tag_in: NoteTagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new tag.
    """
    return await notes_service.create_tag(db, tag_in, current_user.id)


@router.delete("/tags/{id}")
async def delete_tag(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a tag.
    """
    await notes_service.delete_tag(db, id, current_user.id)
    return {"status": "success"}


# =============================================================================
# SHARING ENDPOINTS
# =============================================================================

@router.post("/{id}/share", response_model=NoteShareResponse)
async def share_note(
    id: int,
    share_in: NoteShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Share a note with a user by email.
    """
    return await notes_service.share_note(db, id, current_user.id, share_in)


@router.delete("/{id}/share/{share_id}")
async def delete_share(
    id: int,
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Revoke a share.
    """
    await notes_service.delete_share(db, id, share_id, current_user.id)
    return {"status": "success"}
