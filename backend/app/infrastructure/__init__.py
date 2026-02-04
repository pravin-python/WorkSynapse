"""
WorkSynapse Infrastructure Layer
================================
External service integrations and infrastructure components.

This module provides clean abstractions for:
- Database connections
- Redis caching
- Kafka messaging
- Celery task queue
- File storage
"""

from app.infrastructure.database import (
    AsyncSessionLocal,
    get_db,
    engine,
)

__all__ = [
    "AsyncSessionLocal",
    "get_db",
    "engine",
]
