import pytest
import pytest_asyncio
from app.core.security import create_access_token
from app.models.user.model import User

@pytest.fixture
def auth_headers():
    """Returns a function to generate auth headers for a user."""
    def _get_auth_headers(user: User) -> dict:
        token = create_access_token(subject=str(user.id), role=user.role.value)
        return {"Authorization": f"Bearer {token}"}
    return _get_auth_headers

@pytest_asyncio.fixture
async def regular_user_headers(auth_headers, regular_user):
    """Auth headers for a regular user."""
    return auth_headers(regular_user)

@pytest_asyncio.fixture
async def admin_user_headers(auth_headers, admin_user):
    """Auth headers for an admin user."""
    return auth_headers(admin_user)

@pytest_asyncio.fixture
async def manager_user_headers(auth_headers, manager_user):
    """Auth headers for a manager user."""
    return auth_headers(manager_user)

@pytest_asyncio.fixture
async def super_user_headers(auth_headers, super_user):
    """Auth headers for a super user."""
    return auth_headers(super_user)
