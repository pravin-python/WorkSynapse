"""
Database Session Management
===========================
SQLAlchemy async database configuration and session management.

Features:
- Async PostgreSQL engine with connection pooling
- Session factory for request-scoped sessions
- Dependency injection utilities for FastAPI
- Context manager for CLI operations
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine, 
    AsyncSession, 
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings


# =============================================================================
# ENGINE CONFIGURATION
# =============================================================================

# Engine configuration for different environments
engine_kwargs = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,  # Verify connections before use
}

# Use NullPool for testing to avoid connection issues
if settings.ENVIRONMENT == "testing":
    engine_kwargs["poolclass"] = NullPool
else:
    # Production pool settings
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 3600,  # Recycle connections after 1 hour
    })

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)


# =============================================================================
# SESSION FACTORY
# =============================================================================

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Creates a new session for each request and ensures cleanup.
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions in CLI/background tasks.
    
    Usage:
        async with get_db_session() as db:
            result = await db.execute(...)
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# =============================================================================
# UTILITIES
# =============================================================================

async def init_db() -> None:
    """Initialize database tables."""
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
