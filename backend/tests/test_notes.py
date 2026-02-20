import pytest
from httpx import AsyncClient
from app.models.note.model import Note

@pytest.mark.asyncio
async def test_create_note(client: AsyncClient, regular_user, regular_user_headers):
    """Test creating a new note."""
    response = await client.post(
        "/api/v1/notes/",
        headers=regular_user_headers,
        json={"title": "Test Note", "content": "This is a test note.", "visibility": "PRIVATE"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Note"
    assert data["owner_id"] == regular_user.id

@pytest.mark.asyncio
async def test_get_notes(client: AsyncClient, regular_user, regular_user_headers, note_factory):
    """Test retrieving a list of notes."""
    # Create notes
    await note_factory(regular_user, title="Note 1")
    await note_factory(regular_user, title="Note 2")

    response = await client.get("/api/v1/notes/", headers=regular_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

@pytest.mark.asyncio
async def test_get_note_detail(client: AsyncClient, regular_user, regular_user_headers, note_factory):
    """Test retrieving a specific note."""
    note = await note_factory(regular_user, title="Detail Note")

    response = await client.get(f"/api/v1/notes/{note.id}", headers=regular_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Detail Note"
    assert data["id"] == note.id

@pytest.mark.asyncio
async def test_update_note(client: AsyncClient, regular_user, regular_user_headers, note_factory):
    """Test updating a note."""
    note = await note_factory(regular_user)
    response = await client.put(
        f"/api/v1/notes/{note.id}",
        headers=regular_user_headers,
        json={"title": "Updated Title", "content": "Updated content"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"

@pytest.mark.asyncio
async def test_delete_note(client: AsyncClient, regular_user, regular_user_headers, note_factory):
    """Test deleting a note."""
    note = await note_factory(regular_user)
    response = await client.delete(f"/api/v1/notes/{note.id}", headers=regular_user_headers)
    assert response.status_code == 200

    # Verify deletion (should return 404)
    response = await client.get(f"/api/v1/notes/{note.id}", headers=regular_user_headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_access_denied_for_other_user_note(client: AsyncClient, regular_user_headers, admin_user, note_factory):
    """Test accessing another user's private note is forbidden/not found."""
    # Admin creates a private note
    admin_note = await note_factory(admin_user)

    # Regular user tries to access it
    response = await client.get(f"/api/v1/notes/{admin_note.id}", headers=regular_user_headers)
    assert response.status_code in [403, 404]

@pytest.mark.asyncio
async def test_create_folder(client: AsyncClient, regular_user_headers):
    """Test creating a folder."""
    response = await client.post(
        "/api/v1/notes/folders",
        headers=regular_user_headers,
        json={"name": "My Folder", "color": "#FF0000"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "My Folder"

@pytest.mark.asyncio
async def test_create_tag(client: AsyncClient, regular_user_headers):
    """Test creating a tag."""
    response = await client.post(
        "/api/v1/notes/tags",
        headers=regular_user_headers,
        json={"name": "Important", "color": "#00FF00"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Important"
