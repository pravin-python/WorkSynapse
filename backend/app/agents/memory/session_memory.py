"""
Session Memory
==============

Temporary session-based memory for agents.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SessionData(BaseModel):
    """Data stored in session memory."""

    key: str
    value: Any
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SessionMemory:
    """
    Session memory for agents.

    Provides temporary storage for session-specific data
    with automatic expiration.
    """

    def __init__(
        self,
        agent_id: int,
        session_id: str,
        ttl_hours: int = 2,
    ):
        """
        Initialize session memory.

        Args:
            agent_id: ID of the agent
            session_id: Unique session identifier
            ttl_hours: Default time-to-live in hours
        """
        self.agent_id = agent_id
        self.session_id = session_id
        self.ttl_hours = ttl_hours
        self._data: Dict[str, SessionData] = {}
        self._created_at = datetime.utcnow()

    def set(
        self,
        key: str,
        value: Any,
        ttl_hours: Optional[int] = None,
    ) -> None:
        """
        Store a value in session memory.

        Args:
            key: Data key
            value: Data value
            ttl_hours: Optional custom TTL
        """
        hours = ttl_hours or self.ttl_hours
        expires_at = datetime.utcnow() + timedelta(hours=hours)

        self._data[key] = SessionData(
            key=key,
            value=value,
            expires_at=expires_at,
        )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from session memory.

        Args:
            key: Data key
            default: Default value if not found or expired

        Returns:
            Stored value or default
        """
        self._cleanup_expired()

        if key not in self._data:
            return default

        data = self._data[key]
        if datetime.utcnow() > data.expires_at:
            del self._data[key]
            return default

        return data.value

    def delete(self, key: str) -> bool:
        """
        Delete a value from session memory.

        Args:
            key: Data key

        Returns:
            True if deleted, False if not found
        """
        if key in self._data:
            del self._data[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        self._cleanup_expired()
        return key in self._data

    def keys(self) -> List[str]:
        """Get all active keys."""
        self._cleanup_expired()
        return list(self._data.keys())

    def clear(self) -> None:
        """Clear all session data."""
        self._data.clear()

    def get_all(self) -> Dict[str, Any]:
        """Get all non-expired data as a dictionary."""
        self._cleanup_expired()
        return {key: data.value for key, data in self._data.items()}

    def update(self, data: Dict[str, Any], ttl_hours: Optional[int] = None) -> None:
        """
        Update multiple values at once.

        Args:
            data: Dictionary of key-value pairs
            ttl_hours: Optional custom TTL for all values
        """
        for key, value in data.items():
            self.set(key, value, ttl_hours)

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, data in self._data.items() if now > data.expires_at
        ]
        for key in expired_keys:
            del self._data[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        self._cleanup_expired()
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "created_at": self._created_at.isoformat(),
            "ttl_hours": self.ttl_hours,
            "active_keys": len(self._data),
            "keys": list(self._data.keys()),
        }

    def extend_ttl(self, key: str, hours: int) -> bool:
        """
        Extend the TTL of a value.

        Args:
            key: Data key
            hours: Hours to extend

        Returns:
            True if extended, False if key not found
        """
        if key not in self._data:
            return False

        self._data[key].expires_at += timedelta(hours=hours)
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Export session to dictionary."""
        self._cleanup_expired()
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "created_at": self._created_at.isoformat(),
            "data": {
                key: {
                    "value": data.value,
                    "expires_at": data.expires_at.isoformat(),
                    "created_at": data.created_at.isoformat(),
                }
                for key, data in self._data.items()
            },
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        ttl_hours: int = 2,
    ) -> "SessionMemory":
        """Create session from dictionary."""
        session = cls(
            agent_id=data["agent_id"],
            session_id=data["session_id"],
            ttl_hours=ttl_hours,
        )
        session._created_at = datetime.fromisoformat(data["created_at"])

        for key, item in data.get("data", {}).items():
            session._data[key] = SessionData(
                key=key,
                value=item["value"],
                expires_at=datetime.fromisoformat(item["expires_at"]),
                created_at=datetime.fromisoformat(item["created_at"]),
            )

        return session
