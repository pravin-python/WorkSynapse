import pytest
from httpx import AsyncClient
from app.core.config import settings

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["environment"] == settings.ENVIRONMENT

@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to WorkSynapse API"

@pytest.mark.asyncio
async def test_create_user(user_factory):
    user = await user_factory(email="test@example.com")
    assert user.email == "test@example.com"
    assert user.id is not None
