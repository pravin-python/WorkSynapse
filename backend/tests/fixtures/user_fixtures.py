import pytest
import pytest_asyncio
from faker import Faker
from app.models.user.model import User, UserRole, UserStatus
from app.core.security import get_password_hash

fake = Faker()

@pytest_asyncio.fixture
async def user_factory(db_session):
    """Factory to create users with specific roles and attributes."""
    async def create_user(role=UserRole.DEVELOPER, **kwargs):
        password = kwargs.pop("password", "password123")
        email = kwargs.pop("email", fake.unique.email())
        username = kwargs.pop("username", fake.unique.user_name())
        full_name = kwargs.pop("full_name", fake.name())
        status = kwargs.pop("status", UserStatus.ACTIVE)
        is_active = kwargs.pop("is_active", True)
        is_superuser = kwargs.pop("is_superuser", False)

        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role=role,
            status=status,
            is_active=is_active,
            is_superuser=is_superuser,
            email_verified=True,
            **kwargs
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    return create_user

@pytest_asyncio.fixture
async def regular_user(user_factory):
    return await user_factory(role=UserRole.DEVELOPER)

@pytest_asyncio.fixture
async def admin_user(user_factory):
    return await user_factory(role=UserRole.ADMIN)

@pytest_asyncio.fixture
async def super_user(user_factory):
    return await user_factory(is_superuser=True, role=UserRole.SUPER_ADMIN)

@pytest_asyncio.fixture
async def manager_user(user_factory):
    return await user_factory(role=UserRole.MANAGER)
