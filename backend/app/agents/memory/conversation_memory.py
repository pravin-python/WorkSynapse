"""
Conversation Memory
===================

Short-term conversation memory for agents.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import OrderedDict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConversationMessage(BaseModel):
    """A single conversation message."""

    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationMemory:
    """
    Conversation memory for agents.

    Manages short-term conversation history with configurable
    message limits and time-to-live.
    """

    def __init__(
        self,
        agent_id: int,
        max_messages: int = 50,
        ttl_hours: int = 24,
    ):
        """
        Initialize conversation memory.

        Args:
            agent_id: ID of the agent this memory belongs to
            max_messages: Maximum number of messages to store
            ttl_hours: Time-to-live in hours for messages
        """
        self.agent_id = agent_id
        self.max_messages = max_messages
        self.ttl_hours = ttl_hours
        self._conversations: Dict[str, List[ConversationMessage]] = {}

    def get_conversation(self, thread_id: str) -> List[ConversationMessage]:
        """
        Get messages for a conversation thread.

        Args:
            thread_id: Conversation thread ID

        Returns:
            List of conversation messages
        """
        if thread_id not in self._conversations:
            return []

        # Filter out expired messages
        self._cleanup_expired(thread_id)

        return self._conversations.get(thread_id, [])

    def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a message to a conversation.

        Args:
            thread_id: Conversation thread ID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional message metadata
        """
        if thread_id not in self._conversations:
            self._conversations[thread_id] = []

        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )

        self._conversations[thread_id].append(message)

        # Trim to max messages
        if len(self._conversations[thread_id]) > self.max_messages:
            self._conversations[thread_id] = self._conversations[thread_id][
                -self.max_messages :
            ]

    def add_user_message(
        self,
        thread_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a user message."""
        self.add_message(thread_id, "user", content, metadata)

    def add_assistant_message(
        self,
        thread_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an assistant message."""
        self.add_message(thread_id, "assistant", content, metadata)

    def add_system_message(
        self,
        thread_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a system message."""
        self.add_message(thread_id, "system", content, metadata)

    def get_langchain_messages(self, thread_id: str) -> List[BaseMessage]:
        """
        Get messages in LangChain format.

        Args:
            thread_id: Conversation thread ID

        Returns:
            List of LangChain BaseMessage objects
        """
        messages = self.get_conversation(thread_id)
        lc_messages = []

        for msg in messages:
            if msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
            else:
                lc_messages.append(HumanMessage(content=msg.content))

        return lc_messages

    def get_history_string(
        self,
        thread_id: str,
        last_n: Optional[int] = None,
    ) -> str:
        """
        Get conversation history as a formatted string.

        Args:
            thread_id: Conversation thread ID
            last_n: Optional limit on number of messages

        Returns:
            Formatted conversation history string
        """
        messages = self.get_conversation(thread_id)

        if last_n:
            messages = messages[-last_n:]

        lines = []
        for msg in messages:
            role = msg.role.capitalize()
            lines.append(f"{role}: {msg.content}")

        return "\n".join(lines)

    def clear_conversation(self, thread_id: str) -> None:
        """Clear all messages in a conversation."""
        if thread_id in self._conversations:
            del self._conversations[thread_id]

    def clear_all(self) -> None:
        """Clear all conversations."""
        self._conversations.clear()

    def get_conversation_count(self) -> int:
        """Get the number of active conversations."""
        return len(self._conversations)

    def _cleanup_expired(self, thread_id: str) -> None:
        """Remove expired messages from a conversation."""
        if thread_id not in self._conversations:
            return

        cutoff = datetime.utcnow() - timedelta(hours=self.ttl_hours)
        self._conversations[thread_id] = [
            msg for msg in self._conversations[thread_id] if msg.timestamp > cutoff
        ]

    def to_dict(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Export conversation to a list of dictionaries.

        Args:
            thread_id: Conversation thread ID

        Returns:
            List of message dictionaries
        """
        messages = self.get_conversation(thread_id)
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata,
            }
            for msg in messages
        ]

    def from_dict(self, thread_id: str, messages: List[Dict[str, Any]]) -> None:
        """
        Load conversation from a list of dictionaries.

        Args:
            thread_id: Conversation thread ID
            messages: List of message dictionaries
        """
        self._conversations[thread_id] = [
            ConversationMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg.get("timestamp", datetime.utcnow().isoformat())),
                metadata=msg.get("metadata", {}),
            )
            for msg in messages
        ]
