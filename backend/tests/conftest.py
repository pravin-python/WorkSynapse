import pytest
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock
import uuid
from pydantic import BaseModel

# --- SMARTER MOCKS FOR LANGCHAIN ---

# Helper to create a mock package
def create_mock_package(name):
    m = MagicMock()
    m.__path__ = []  # This makes it a package
    m.__spec__ = MagicMock() # Ensure __spec__ exists
    sys.modules[name] = m
    return m

# Mock langchain and its submodules
langchain = create_mock_package("langchain")
langchain.memory = create_mock_package("langchain.memory")
langchain.schema = create_mock_package("langchain.schema")
langchain.schema.messages = create_mock_package("langchain.schema.messages")

# Pydantic-compatible message mocks
class MockBaseMessage(BaseModel):
    content: str
    type: str = "base"

class MockSystemMessage(MockBaseMessage):
    type: str = "system"

class MockHumanMessage(MockBaseMessage):
    type: str = "human"

class MockAIMessage(MockBaseMessage):
    type: str = "ai"

# Mock langchain_core
langchain_core = create_mock_package("langchain_core")
messages_mock = create_mock_package("langchain_core.messages")
messages_mock.BaseMessage = MockBaseMessage
messages_mock.SystemMessage = MockSystemMessage
messages_mock.HumanMessage = MockHumanMessage
messages_mock.AIMessage = MockAIMessage
sys.modules["langchain_core.messages"] = messages_mock
langchain_core.messages = messages_mock

# Mock other langchain related packages
create_mock_package("langchain_core.language_models")
create_mock_package("langchain_core.runnables")
create_mock_package("langchain_core.tools")
create_mock_package("langchain_core.callbacks")
create_mock_package("langchain_core.documents")
create_mock_package("langchain_openai")
create_mock_package("langchain_anthropic")
create_mock_package("langchain_google_genai")
create_mock_package("langchain_ollama")
create_mock_package("langchain_huggingface")
create_mock_package("langchain_aws")
create_mock_package("langchain_postgres")

# Mock langgraph
langgraph = create_mock_package("langgraph")
langgraph.graph = create_mock_package("langgraph.graph")
langgraph.prebuilt = create_mock_package("langgraph.prebuilt")
langgraph.checkpoint = create_mock_package("langgraph.checkpoint")
langgraph.checkpoint.memory = create_mock_package("langgraph.checkpoint.memory")

# Mock infrastructure
create_mock_package("aiokafka")
celery = create_mock_package("celery")
celery.shared_task = MagicMock(return_value=lambda x: x) # Mock shared_task decorator

# --- DATABASE PATCHES ---

# Patch PostgreSQL specific types for SQLite compatibility
import sqlalchemy.dialects.postgresql
from sqlalchemy.types import TypeDecorator, JSON, String, CHAR

class MockJSONB(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(JSON())

class MockUUID(TypeDecorator):
    impl = String
    cache_ok = True

    def __init__(self, as_uuid=True, **kwargs):
        # Eat as_uuid argument as String doesn't support it
        super().__init__(**kwargs)

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value) if isinstance(value, str) else value

# Apply patches
sqlalchemy.dialects.postgresql.JSONB = MockJSONB
sqlalchemy.dialects.postgresql.UUID = MockUUID

# Now import the rest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.session import get_db
from app.models.base import Base
from app.core.config import settings

# Override settings for testing
settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for test database
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False,
)

# Create async session factory
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """Create tables once for the session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture that provides a fresh database session for each test.
    Using a nested transaction (savepoint) to rollback changes after each test.
    This is faster than recreating tables.
    """
    connection = await engine.connect()
    trans = await connection.begin()

    # Create a session bound to the connection
    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    async with session_factory() as session:
        yield session
        await session.close()

    # Rollback the transaction to discard changes
    await trans.rollback()
    await connection.close()

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that provides an authenticated HTTP client.
    Overrides the get_db dependency to use the test session.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()

# Import fixtures using absolute paths
from backend.tests.fixtures.user_fixtures import *
from backend.tests.fixtures.auth_fixtures import *
from backend.tests.fixtures.note_fixtures import *
from backend.tests.fixtures.project_fixtures import *
from backend.tests.fixtures.agent_fixtures import *
