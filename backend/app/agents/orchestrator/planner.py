"""
Execution Planner
=================

Plans the execution steps for an agent.
"""

from typing import List, Dict, Any
from langchain_core.messages import BaseMessage
from langchain_core.language_models import BaseChatModel

class ExecutionPlanner:
    """
    Plans the execution steps for an agent.
    """
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def plan(self, messages: List[BaseMessage]) -> List[str]:
        # Simple planning: just return default plan or use LLM to break down task
        # For now, placeholder.
        return ["understand_request", "execute_tools", "finalize_response"]
