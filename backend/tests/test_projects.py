import pytest
from httpx import AsyncClient
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_get_projects_empty(client: AsyncClient, regular_user_headers):
    """Test getting projects when none exist."""
    response = await client.get("/api/v1/projects/", headers=regular_user_headers)
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_projects_with_data(client: AsyncClient, regular_user, regular_user_headers, project_factory, db_session):
    """Test getting projects when some exist."""
    project = await project_factory(regular_user)

    from app.models.project.model import ProjectMember, MemberRole

    # Use timezone-aware datetime
    member = ProjectMember(
        project_id=project.id,
        user_id=regular_user.id,
        role=MemberRole.OWNER,
        joined_at=datetime.now(timezone.utc)
    )
    db_session.add(member)
    await db_session.commit()

    response = await client.get("/api/v1/projects/", headers=regular_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["id"] == project.id
