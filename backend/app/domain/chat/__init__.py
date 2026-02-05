"""
Chat Domain
===========
Chat-related models, schemas, and services.

Re-exports from the models layer for backward compatibility.
"""

from app.models.chat.model import (
    Conversation,
    Message,
)

__all__ = [
    "Conversation",
    "Message",
]
