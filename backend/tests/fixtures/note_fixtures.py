import pytest
import pytest_asyncio
from app.models.note.model import Note, NoteFolder, NoteTag, NoteVisibility
from faker import Faker

fake = Faker()

@pytest_asyncio.fixture
async def note_factory(db_session):
    async def create_note(owner, **kwargs):
        title = kwargs.pop("title", fake.sentence())
        content = kwargs.pop("content", fake.text())
        visibility = kwargs.pop("visibility", NoteVisibility.PRIVATE)
        is_pinned = kwargs.pop("is_pinned", False)
        is_archived = kwargs.pop("is_archived", False)

        note = Note(
            title=title,
            content=content,
            owner_id=owner.id,
            visibility=visibility,
            is_pinned=is_pinned,
            is_archived=is_archived,
            **kwargs
        )
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)
        return note
    return create_note

@pytest_asyncio.fixture
async def folder_factory(db_session):
    async def create_folder(owner, **kwargs):
        name = kwargs.pop("name", fake.word())
        color = kwargs.pop("color", "#FFFFFF")

        folder = NoteFolder(
            name=name,
            owner_id=owner.id,
            color=color,
            **kwargs
        )
        db_session.add(folder)
        await db_session.commit()
        await db_session.refresh(folder)
        return folder
    return create_folder
