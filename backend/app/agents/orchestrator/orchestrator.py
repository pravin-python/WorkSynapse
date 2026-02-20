"""
Agent Orchestrator
==================

Main orchestrator for dynamic agent execution.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, AsyncIterator
from pydantic import BaseModel

from app.agents.orchestrator.execution_loop import ExecutionLoop
from app.agents.orchestrator.planner import ExecutionPlanner
from app.agents.memory.memory_manager import get_memory_manager
from app.agents.orchestrator.config import get_orchestrator_config
from app.agents.orchestrator.security import SecurityGuard, get_security_guard
from app.agents.orchestrator.exceptions import OrchestratorError, PromptInjectionError

logger = logging.getLogger(__name__)

class ExecutionResult(BaseModel):
    """Result of agent execution."""
    response: str
    tool_calls: List[Dict[str, Any]] = []
    thread_id: str = ""
    duration_ms: int = 0

class AgentOrchestrator:
    """
    Main orchestrator for dynamic agent execution.
    """

    def __init__(self):
        self.config = get_orchestrator_config()
        self.memory_manager = get_memory_manager()
        self.security_guard = get_security_guard()

    async def run(
        self,
        agent_config: Dict[str, Any],
        message: str,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Run an agent with a message.
        """
        start_time = time.time()
        agent_id = agent_config.get("id", 0)
        thread_id = thread_id or str(uuid.uuid4())

        try:
            # 0. Security Check
            if not self.security_guard.validate_input(message, agent_config):
                raise PromptInjectionError()

            # 1. Execution Loop
            loop = ExecutionLoop(agent_config, self.memory_manager)
            result = await loop.run(message, thread_id, agent_id)

            # 2. Store Memory
            # Persist User and Assistant messages to ConversationMemory
            # We assume ConversationMemory is the high-level chat history.
            # Intermediate tool steps are generally not stored in "chat history" but in "execution logs".

            await self.memory_manager.add_to_conversation(
                agent_id, thread_id, "user", message
            )

            # If response is empty (e.g. tool loop fail), we should handle it.
            response = result.get("response", "")
            if response:
                await self.memory_manager.add_to_conversation(
                    agent_id, thread_id, "assistant", response
                )

            duration_ms = int((time.time() - start_time) * 1000)

            return ExecutionResult(
                response=response,
                tool_calls=result.get("tool_calls", []),
                thread_id=thread_id,
                duration_ms=duration_ms
            )

        except Exception as e:
            logger.error(f"Orchestrator run error: {e}", exc_info=True)
            raise OrchestratorError(str(e))

# Global instance
_orchestrator: Optional[AgentOrchestrator] = None

def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
