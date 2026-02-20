"""
Memory Manager
==============

Central manager for all agent memory systems.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.memory.conversation_memory import ConversationMemory
from app.agents.memory.vector_memory import VectorMemory
from app.agents.memory.session_memory import SessionMemory
from app.agents.orchestrator.config import get_orchestrator_config, MemoryConfig
from app.agents.orchestrator.exceptions import MemoryError

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central manager for agent memory systems.

    Manages conversation, vector, and session memory for agents.
    Provides a unified interface for memory operations.
    """

    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize the memory manager.

        Args:
            config: Optional memory configuration
        """
        orchestrator_config = get_orchestrator_config()
        self.config = config or orchestrator_config.memory
        
        # Memory caches
        self._conversation_memories: Dict[int, ConversationMemory] = {}
        self._vector_memories: Dict[int, VectorMemory] = {}
        self._session_memories: Dict[str, SessionMemory] = {}

    def get_conversation_memory(
        self,
        agent_id: int,
        max_messages: Optional[int] = None,
        ttl_hours: Optional[int] = None,
    ) -> ConversationMemory:
        """
        Get or create conversation memory for an agent.

        Args:
            agent_id: Agent ID
            max_messages: Optional max messages override
            ttl_hours: Optional TTL override

        Returns:
            ConversationMemory instance
        """
        if agent_id not in self._conversation_memories:
            self._conversation_memories[agent_id] = ConversationMemory(
                agent_id=agent_id,
                max_messages=max_messages or self.config.conversation_max_messages,
                ttl_hours=ttl_hours or self.config.conversation_ttl_hours,
            )

        return self._conversation_memories[agent_id]

    def get_vector_memory(
        self,
        agent_id: int,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
        k_results: Optional[int] = None,
    ) -> VectorMemory:
        """
        Get or create vector memory for an agent.

        Args:
            agent_id: Agent ID
            collection_name: Optional collection name
            embedding_model: Optional embedding model
            k_results: Optional k results

        Returns:
            VectorMemory instance
        """
        if agent_id not in self._vector_memories:
            self._vector_memories[agent_id] = VectorMemory(
                agent_id=agent_id,
                collection_name=collection_name or f"{self.config.vector_collection_prefix}{agent_id}",
                embedding_model=embedding_model or self.config.embedding_model,
                k_results=k_results or self.config.vector_k_results,
            )

        return self._vector_memories[agent_id]

    def get_session_memory(
        self,
        agent_id: int,
        session_id: str,
        ttl_hours: Optional[int] = None,
    ) -> SessionMemory:
        """
        Get or create session memory for an agent session.

        Args:
            agent_id: Agent ID
            session_id: Session identifier
            ttl_hours: Optional TTL override

        Returns:
            SessionMemory instance
        """
        cache_key = f"{agent_id}:{session_id}"

        if cache_key not in self._session_memories:
            self._session_memories[cache_key] = SessionMemory(
                agent_id=agent_id,
                session_id=session_id,
                ttl_hours=ttl_hours or self.config.session_ttl_hours,
            )

        return self._session_memories[cache_key]

    async def add_to_conversation(
        self,
        agent_id: int,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a message to conversation memory.

        Args:
            agent_id: Agent ID
            thread_id: Conversation thread ID
            role: Message role
            content: Message content
            metadata: Optional metadata
        """
        memory = self.get_conversation_memory(agent_id)
        memory.add_message(thread_id, role, content, metadata)

    async def get_conversation_history(
        self,
        agent_id: int,
        thread_id: str,
        as_langchain: bool = False,
    ):
        """
        Get conversation history.

        Args:
            agent_id: Agent ID
            thread_id: Conversation thread ID
            as_langchain: Whether to return LangChain messages

        Returns:
            List of messages
        """
        memory = self.get_conversation_memory(agent_id)

        if as_langchain:
            return memory.get_langchain_messages(thread_id)
        else:
            return memory.get_conversation(thread_id)

    async def add_to_vector_memory(
        self,
        agent_id: int,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add content to vector memory.

        Args:
            agent_id: Agent ID
            content: Content to store
            metadata: Optional metadata

        Returns:
            Document ID
        """
        memory = self.get_vector_memory(agent_id)
        await memory.initialize()
        return await memory.add(content, metadata)

    async def search_vector_memory(
        self,
        agent_id: int,
        query: str,
        k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search vector memory.

        Args:
            agent_id: Agent ID
            query: Search query
            k: Number of results

        Returns:
            List of matching documents
        """
        memory = self.get_vector_memory(agent_id)
        await memory.initialize()
        return await memory.search(query, k)

    def set_session_value(
        self,
        agent_id: int,
        session_id: str,
        key: str,
        value: Any,
    ) -> None:
        """
        Set a session value.

        Args:
            agent_id: Agent ID
            session_id: Session ID
            key: Data key
            value: Data value
        """
        memory = self.get_session_memory(agent_id, session_id)
        memory.set(key, value)

    def get_session_value(
        self,
        agent_id: int,
        session_id: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get a session value.

        Args:
            agent_id: Agent ID
            session_id: Session ID
            key: Data key
            default: Default value

        Returns:
            Stored value or default
        """
        memory = self.get_session_memory(agent_id, session_id)
        return memory.get(key, default)

    def clear_agent_memory(self, agent_id: int) -> None:
        """
        Clear all memory for an agent.

        Args:
            agent_id: Agent ID
        """
        # Clear conversation memory
        if agent_id in self._conversation_memories:
            self._conversation_memories[agent_id].clear_all()
            del self._conversation_memories[agent_id]

        # Clear vector memory
        if agent_id in self._vector_memories:
            # Note: This doesn't clear persisted vector data
            del self._vector_memories[agent_id]

        # Clear session memories
        keys_to_remove = [
            key for key in self._session_memories.keys()
            if key.startswith(f"{agent_id}:")
        ]
        for key in keys_to_remove:
            self._session_memories[key].clear()
            del self._session_memories[key]

        logger.info(f"Cleared all memory for agent {agent_id}")

    def get_memory_stats(self, agent_id: int) -> Dict[str, Any]:
        """
        Get memory statistics for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            Dictionary of memory statistics
        """
        stats = {
            "agent_id": agent_id,
            "conversation": {},
            "vector": {},
            "sessions": [],
        }

        if agent_id in self._conversation_memories:
            memory = self._conversation_memories[agent_id]
            stats["conversation"] = {
                "active_conversations": memory.get_conversation_count(),
            }

        if agent_id in self._vector_memories:
            # Vector stats would require async operation
            stats["vector"] = {"initialized": True}

        # Session stats
        for key, session in self._session_memories.items():
            if key.startswith(f"{agent_id}:"):
                stats["sessions"].append(session.get_stats())

        return stats


# Global memory manager instance
_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _manager
    if _manager is None:
        _manager = MemoryManager()
    return _manager
