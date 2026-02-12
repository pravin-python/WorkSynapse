from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, select, func

from app.models.note.model import (
    Note, NoteFolder, NoteTag, NoteShare, 
    SharePermission, note_tag_map
)
from app.schemas.note import (
    NoteCreate, NoteUpdate, 
    NoteFolderCreate, NoteFolderUpdate,
    NoteTagCreate, NoteTagUpdate,
    NoteShareCreate, NoteShareUpdate
)
from app.core.exceptions import (
    NotFoundException, 
    ForbiddenException, 
    BadRequestException
)

class NotesService:
    
    # =========================================================================
    # NOTES CRUD
    # =========================================================================
    
    async def get_notes(
        self, 
        db: Session, 
        user_id: int, 
        search: Optional[str] = None,
        folder_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        is_starred: Optional[bool] = None,
        is_shared: Optional[bool] = None,
        skip: int = 0, 
        limit: int = 50
    ) -> Tuple[List[Note], int]:
        """
        Get notes with filtering.
        Handles ownership and shared access.
        """
        
        # Base query
        stmt = select(Note)
        
        conditions = []
        
        # Access Control Logic
        if is_shared:
            # Only return notes shared WITH the user
            # We use join here as it's more direct for specific filtering
            stmt = stmt.join(NoteShare, Note.id == NoteShare.note_id)
            conditions.append(NoteShare.shared_with_user_id == user_id)
        else:
            # Return owned notes OR shared notes
            conditions.append(
                or_(
                    Note.owner_id == user_id,
                    Note.shares.any(NoteShare.shared_with_user_id == user_id)
                )
            )

        # Filters
        if folder_id:
            conditions.append(Note.folder_id == folder_id)
            
        if is_starred is not None:
             conditions.append(Note.is_starred == is_starred)
             
        if search:
            search_filter = or_(
                Note.title.ilike(f"%{search}%"),
                Note.content.ilike(f"%{search}%")
            )
            conditions.append(search_filter)

        if tag_id:
            # Join with tag map to filter
            stmt = stmt.join(note_tag_map, Note.id == note_tag_map.c.note_id)
            conditions.append(note_tag_map.c.tag_id == tag_id)
            
        # Apply conditions
        if conditions:
            stmt = stmt.where(and_(*conditions))
            
        # Count total
        # Create a separate count query to avoid eager loading issues
        count_query = select(func.count(Note.id)).select_from(stmt.subquery())
        # Ideally, we construct count without options, but stmt here might have joins from tag/share
        # SQLAlchemy 1.4/2.0 handle subquery select_from smartly usually.
        # But simpler:
        # count_stmt = select(func.count()).select_from(stmt.alias()) -- alias() ensures valid subquery
        count_res = await db.execute(count_query)
        total = count_res.scalar() or 0
        
        # Add filtering options for main query
        stmt = stmt.options(
            joinedload(Note.folder),
            joinedload(Note.tags),
            joinedload(Note.shares)
        ).order_by(Note.updated_at.desc())
        
        # Pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().unique().all(), total

    async def get_note(self, db: Session, note_id: int, user_id: int) -> Note:
        """Get single note if user has access."""
        res = await db.execute(
            select(Note).options(
                joinedload(Note.folder),
                joinedload(Note.tags),
                joinedload(Note.shares),
            ).filter(Note.id == note_id)
        )
        note = res.scalars().first()
        
        if not note:
            raise NotFoundException("Note not found")
            
        # Check access
        if note.owner_id != user_id:
            # Check share
            res = await db.execute(
                select(NoteShare).filter(
                    NoteShare.note_id == note_id,
                    NoteShare.shared_with_user_id == user_id,
                )
            )
            share = res.scalars().first()
            if not share:
                 raise ForbiddenException("You do not have access to this note")
        
        return note

    async def create_note(self, db: Session, note_in: NoteCreate, user_id: int) -> Note:
        """Create a new note."""
        # Verify folder ownership if provided
        if note_in.folder_id:
            res = await db.execute(
                select(NoteFolder).filter(
                    NoteFolder.id == note_in.folder_id,
                    NoteFolder.owner_id == user_id,
                )
            )
            folder = res.scalars().first()
            if not folder:
                raise BadRequestException("Invalid folder")

        note_data = note_in.model_dump(exclude={"tag_ids"})
        note = Note(**note_data, owner_id=user_id)
        db.add(note)
        await db.flush() # to get ID
        
        # Tags
        if note_in.tag_ids:
            res = await db.execute(
                select(NoteTag).filter(
                    NoteTag.id.in_(note_in.tag_ids),
                    NoteTag.owner_id == user_id,
                )
            )
            tags = res.scalars().all()
            note.tags = tags

        await db.commit()
        await db.refresh(note)
        return note

    async def update_note(self, db: Session, note_id: int, note_in: NoteUpdate, user_id: int) -> Note:
        """Update a note."""
        note = await self.get_note(db, note_id, user_id)
        
        # Check edit permission
        if note.owner_id != user_id:
            # Check share permission
            res = await db.execute(
                select(NoteShare).filter(
                    NoteShare.note_id == note_id,
                    NoteShare.shared_with_user_id == user_id,
                )
            )
            share = res.scalars().first()
            if not share or share.permission != SharePermission.EDIT:
                raise ForbiddenException("Read only access")

        # Update fields
        update_data = note_in.model_dump(exclude_unset=True, exclude={"tag_ids"})
        for field, value in update_data.items():
            setattr(note, field, value)
            
        # Update tags (only owner can change tags? or editors too? Assuming editor can)
        if note_in.tag_ids is not None:
            res = await db.execute(
                select(NoteTag).filter(
                    NoteTag.id.in_(note_in.tag_ids),
                    NoteTag.owner_id == note.owner_id,
                )
            )
            tags = res.scalars().all()
            if note.owner_id == user_id:
                note.tags = tags
        
        await db.commit()
        await db.refresh(note)
        return note

    async def delete_note(self, db: Session, note_id: int, user_id: int):
        """Delete a note."""
        note = await self.get_note(db, note_id, user_id)
        if note.owner_id != user_id:
            raise ForbiddenException("Only owner can delete note")
            
        await db.delete(note)
        await db.commit()

    async def star_note(self, db: Session, note_id: int, user_id: int, is_starred: bool) -> Note:
        """Star/Unstar a note."""
        # NOTE: Current model puts `is_starred` on the NOTE itself.
        # This means if I star it, everyone sees it starred?
        # Requirement: "Starred is per owner (later can expand per user)."
        # So only owner can star. Shared users cannot star (or it won't persist for them personally).

        note = await self.get_note(db, note_id, user_id)
        if note.owner_id != user_id:
            raise ForbiddenException("Only owner can star notes (v1 limitation)")

        note.is_starred = is_starred
        await db.commit()
        await db.refresh(note)
        return note

    # =========================================================================
    # FOLDERS
    # =========================================================================

    async def get_folders(self, db: Session, user_id: int) -> List[NoteFolder]:
        res = await db.execute(select(NoteFolder).filter(NoteFolder.owner_id == user_id))
        return res.scalars().all()

    async def create_folder(self, db: Session, folder_in: NoteFolderCreate, user_id: int) -> NoteFolder:
        # Check unique
        res = await db.execute(
            select(NoteFolder).filter(
                NoteFolder.owner_id == user_id,
                NoteFolder.name == folder_in.name,
            )
        )
        exists = res.scalars().first()
        if exists:
            raise BadRequestException("Folder with this name already exists")

        folder = NoteFolder(**folder_in.model_dump(), owner_id=user_id)
        db.add(folder)
        await db.commit()
        await db.refresh(folder)
        return folder
        
    async def delete_folder(self, db: Session, folder_id: int, user_id: int):
        res = await db.execute(
            select(NoteFolder).filter(
                NoteFolder.id == folder_id,
                NoteFolder.owner_id == user_id,
            )
        )
        folder = res.scalars().first()
        if not folder:
            raise NotFoundException("Folder not found")
        # Notes will set folder_id to NULL due to ondelete="SET NULL" in model
        await db.delete(folder)
        await db.commit()

    # =========================================================================
    # TAGS
    # =========================================================================

    async def get_tags(self, db: Session, user_id: int) -> List[NoteTag]:
        res = await db.execute(select(NoteTag).filter(NoteTag.owner_id == user_id))
        return res.scalars().all()
        
    async def create_tag(self, db: Session, tag_in: NoteTagCreate, user_id: int) -> NoteTag:
        res = await db.execute(
            select(NoteTag).filter(
                NoteTag.owner_id == user_id,
                NoteTag.name == tag_in.name,
            )
        )
        exists = res.scalars().first()
        if exists:
            raise BadRequestException("Tag with this name already exists")

        tag = NoteTag(**tag_in.model_dump(), owner_id=user_id)
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        return tag

    async def delete_tag(self, db: Session, tag_id: int, user_id: int):
        res = await db.execute(
            select(NoteTag).filter(
                NoteTag.id == tag_id,
                NoteTag.owner_id == user_id,
            )
        )
        tag = res.scalars().first()
        if not tag:
            raise NotFoundException("Tag not found")
        await db.delete(tag)
        await db.commit()

    # =========================================================================
    # SHARING
    # =========================================================================

    async def share_note(self, db: Session, note_id: int, user_id: int, share_in: NoteShareCreate) -> NoteShare:
        note = await self.get_note(db, note_id, user_id)
        if note.owner_id != user_id:
            raise ForbiddenException("Only owner can share")

        # Find user by email
        from app.models import User # Deferred import
        res = await db.execute(select(User).filter(User.email == share_in.email))
        target_user = res.scalars().first()
        if not target_user:
            raise NotFoundException(f"User with email {share_in.email} not found")
        
        if target_user.id == user_id:
            raise BadRequestException("Cannot share with yourself")

        # Check existing share
        res = await db.execute(
            select(NoteShare).filter(
                NoteShare.note_id == note_id,
                NoteShare.shared_with_user_id == target_user.id,
            )
        )
        existing = res.scalars().first()
        
        if existing:
            # Update permission
            existing.permission = share_in.permission
            await db.commit()
            await db.refresh(existing)
            return existing
            
        share = NoteShare(
            note_id=note_id,
            shared_with_user_id=target_user.id,
            shared_by_user_id=user_id,
            permission=share_in.permission
        )
        db.add(share)
        await db.commit()
        await db.refresh(share)
        return share

    async def delete_share(self, db: Session, note_id: int, share_id: int, user_id: int):
        note = await self.get_note(db, note_id, user_id)
        if note.owner_id != user_id:
             raise ForbiddenException("Only owner can revoke shares")
             
        res = await db.execute(select(NoteShare).filter(NoteShare.id == share_id))
        share = res.scalars().first()
        if share:
            await db.delete(share)
            await db.commit()

notes_service = NotesService()
