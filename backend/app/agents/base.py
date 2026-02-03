from typing import List, Dict, Any, Optional
import abc

class BaseAgent(abc.ABC):
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.context: List[Dict[str, str]] = []

    @abc.abstractmethod
    async def process_message(self, message: str) -> str:
        """Process an incoming user message and return a response."""
        pass

    def add_context(self, role: str, content: str):
        self.context.append({"role": role, "content": content})

    async def query_vector_db(self, query: str) -> List[Any]:
        """Placeholder for vector DB retrieval"""
        return []
