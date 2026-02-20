"""
Agent Tester
============

Test agent responses end-to-end.
"""

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.runtime.agent_runtime import get_agent_runtime

class AgentTester:
    """
    Test agent functionality end-to-end.
    """
    def __init__(self):
        self.runtime = get_agent_runtime()

    async def test_agent(self, db: AsyncSession, agent_id: int, message: str, user_id: int) -> Dict[str, Any]:
        """
        Simulate a conversation with an agent.
        """
        try:
            result = await self.runtime.execute_agent(db, agent_id, message, user_id)
            return {
                "success": True,
                "response": result.response,
                "tool_calls": result.tool_calls,
                "duration_ms": result.duration_ms
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
