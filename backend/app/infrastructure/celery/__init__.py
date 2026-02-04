"""
Celery Infrastructure
=====================
Celery task queue for background processing.
"""

from app.infrastructure.celery.app import celery_app

__all__ = [
    "celery_app",
]
