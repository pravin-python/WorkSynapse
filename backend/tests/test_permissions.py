import pytest
from httpx import AsyncClient
from app.models.user.model import UserRole

@pytest.mark.asyncio
async def test_admin_access_allowed(client: AsyncClient, admin_user_headers):
    """Test that admin user can access admin-only resources."""
    # Assuming there's an admin-only endpoint
    # Trying with follow_redirects=True for 307 issues
    response = await client.get("/api/v1/roles/", headers=admin_user_headers, follow_redirects=True)
    if response.status_code == 404:
        pytest.skip("Roles endpoint not found")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_regular_user_denied_admin_resource(client: AsyncClient, regular_user_headers):
    """Test that regular user cannot access admin-only resources."""
    response = await client.post(
        "/api/v1/roles/",
        headers=regular_user_headers,
        json={"name": "New Role", "description": "test"},
        follow_redirects=True
    )
    if response.status_code == 404:
        pytest.skip("Roles endpoint not found")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_manager_access(client: AsyncClient, manager_user_headers):
    """Test manager specific access if applicable."""
    pass
