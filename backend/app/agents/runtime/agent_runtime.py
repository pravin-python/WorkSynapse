"""
Agent Runtime
=============

High-level runtime for AI Agents.
Handling request lifecycle, context, and orchestration dispatch.
"""

import logging
from typing import Any, Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.agents.orchestrator.orchestrator import get_orchestrator, ExecutionResult
from app.agents.runtime.execution_context import ExecutionContext
from app.services.agent import agent_service
from app.models.agent.model import Agent, AgentUserPermission

logger = logging.getLogger(__name__)

class AgentRuntime:
    """
    High-level runtime for AI Agents.
    Handling request lifecycle, context, and orchestration dispatch.
    """

    def __init__(self):
        self.orchestrator = get_orchestrator()

    async def execute_agent(
        self,
        db: AsyncSession,
        agent_id: int,
        message: str,
        user_id: int,
        thread_id: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute an agent request.
        """
        # 1. Fetch Agent Config with Tools
        query = select(Agent).options(
            selectinload(Agent.tools)
        ).filter(Agent.id == agent_id)

        result = await db.execute(query)
        agent = result.scalars().first()

        if not agent:
             raise ValueError(f"Agent {agent_id} not found")

        # 2. Fetch User Permissions
        perm_query = select(AgentUserPermission).filter(
            AgentUserPermission.agent_id == agent_id,
            AgentUserPermission.user_id == user_id
        )
        perm_result = await db.execute(perm_query)
        user_perm = perm_result.scalars().first()

        # Construct Permissions Dict
        permissions = {
            "can_use": True, # Default if accessing public/creator agent, strictly checked in service usually
            "can_execute_code": False, # Default safe
            "can_access_internet": False # Default safe
        }

        if user_perm:
            permissions["can_use"] = user_perm.can_use
            # specific permissions could be mapped if they existed in the model
            # For now we assume standard permissions or map from custom fields if added later

        # 3. Map Tools
        tool_configs = []
        if agent.tools:
            for tool in agent.tools:
                tool_configs.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.function_schema
                })

        # 4. Construct Config
        agent_config = {
            "id": agent.id,
            "name": agent.name,
            "system_prompt": agent.system_prompt,
            "llm_provider": agent.llm_provider.value if hasattr(agent.llm_provider, 'value') else str(agent.llm_provider),
            "model_name": agent.llm_model,
            "tools": tool_configs,
            "permissions": permissions,
            "goal": agent.goals[0] if agent.goals else "",
            "instruction": "",
            "rag_enabled": False, # Could be added to Agent model
            "max_steps": 15
        }

        # 5. Create Context
        context = ExecutionContext(
            agent_id=agent_id,
            user_id=str(user_id),
            thread_id=thread_id
        )

        # 6. Invoke Orchestrator
        try:
            result = await self.orchestrator.run(
                agent_config=agent_config,
                message=message,
                thread_id=thread_id
            )
            return result
        except Exception as e:
            logger.error(f"Runtime execution failed: {e}")
            raise

# Global Runtime
_runtime = None

def get_agent_runtime() -> AgentRuntime:
    global _runtime
    if _runtime is None:
        _runtime = AgentRuntime()
    return _runtime
