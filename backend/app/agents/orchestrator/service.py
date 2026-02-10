"""
Agent Orchestrator Service
==========================

Service layer for agent CRUD operations and execution.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_

from app.agents.orchestrator.models import (
    OrchestratorAgent,
    OrchestratorConversation,
    AgentExecution,
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    ExecutionRequest,
)
from app.agents.orchestrator.core import AgentOrchestrator, get_orchestrator, ExecutionResult
from app.agents.orchestrator.exceptions import AgentNotFoundError, OrchestratorError

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service for managing agents.

    Provides CRUD operations for agents and handles
    agent execution through the orchestrator.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the agent service.

        Args:
            db: Database session
        """
        self.db = db
        self.orchestrator = get_orchestrator()

    async def create_agent(
        self,
        data: AgentCreate,
        created_by: Optional[UUID] = None,
    ) -> OrchestratorAgent:
        """
        Create a new agent.

        Args:
            data: Agent creation data
            created_by: User ID who created the agent

        Returns:
            Created OrchestratorAgent model
        """
        # Convert tools to list of dicts if needed
        tools_data = [
            t.model_dump() if hasattr(t, "model_dump") else t
            for t in data.tools
        ]

        # Convert permissions
        permissions_data = data.permissions.model_dump() if hasattr(data.permissions, "model_dump") else data.permissions

        # Convert advanced config
        config_data = data.config.model_dump() if hasattr(data.config, "model_dump") else data.config

        agent = OrchestratorAgent(
            name=data.name,
            description=data.description,
            system_prompt=data.system_prompt,
            goal=data.goal,
            identity_guidance=data.identity_guidance,
            llm_provider=data.llm_provider.value,
            model_name=data.model_name,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            tools=tools_data,
            memory_type=data.memory_type.value,
            enable_long_term_memory=data.enable_long_term_memory,
            memory_config=data.memory_config,
            permissions=permissions_data,
            config=config_data,
            is_public=data.is_public,
            created_by=created_by,
        )

        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)

        logger.info(f"Created agent: {agent.id} - {agent.name}")
        return agent

    async def get_agent(self, agent_id: int) -> OrchestratorAgent:
        """
        Get an agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            OrchestratorAgent model

        Raises:
            AgentNotFoundError: If agent not found
        """
        result = await self.db.execute(
            select(OrchestratorAgent).where(OrchestratorAgent.id == agent_id)
        )
        agent = result.scalar_one_or_none()

        if not agent:
            raise AgentNotFoundError(agent_id)

        return agent

    async def list_agents(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[UUID] = None,
        include_public: bool = True,
    ) -> Dict[str, Any]:
        """
        List agents with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            user_id: Filter by owner
            include_public: Include public agents

        Returns:
            Dict with agents, total, and pagination info
        """
        # Build query
        conditions = []
        if user_id:
            if include_public:
                conditions.append(
                    (OrchestratorAgent.created_by == user_id) | (OrchestratorAgent.is_public == True)
                )
            else:
                conditions.append(OrchestratorAgent.created_by == user_id)

        query = select(OrchestratorAgent)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(OrchestratorAgent.created_at.desc())

        # Get total count
        count_query = select(OrchestratorAgent.id)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = len(count_result.all())

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        agents = result.scalars().all()

        return {
            "agents": agents,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + len(agents) < total,
        }

    async def update_agent(
        self,
        agent_id: int,
        data: AgentUpdate,
        user_id: Optional[UUID] = None,
    ) -> OrchestratorAgent:
        """
        Update an agent.

        Args:
            agent_id: Agent ID
            data: Update data
            user_id: User making the update (for permission check)

        Returns:
            Updated OrchestratorAgent model
        """
        agent = await self.get_agent(agent_id)

        # Update fields
        update_data = data.model_dump(exclude_unset=True)

        # Handle nested objects
        if "tools" in update_data:
            update_data["tools"] = [
                t.model_dump() if hasattr(t, "model_dump") else t
                for t in update_data["tools"]
            ]
        if "permissions" in update_data:
            update_data["permissions"] = (
                update_data["permissions"].model_dump()
                if hasattr(update_data["permissions"], "model_dump")
                else update_data["permissions"]
            )
        if "config" in update_data:
            update_data["config"] = (
                update_data["config"].model_dump()
                if hasattr(update_data["config"], "model_dump")
                else update_data["config"]
            )
        if "llm_provider" in update_data:
            update_data["llm_provider"] = update_data["llm_provider"].value
        if "memory_type" in update_data:
            update_data["memory_type"] = update_data["memory_type"].value

        for key, value in update_data.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        await self.db.commit()
        await self.db.refresh(agent)

        logger.info(f"Updated agent: {agent.id}")
        return agent

    async def delete_agent(
        self,
        agent_id: int,
        user_id: Optional[UUID] = None,
    ) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: Agent ID
            user_id: User making the deletion (for permission check)

        Returns:
            True if deleted
        """
        agent = await self.get_agent(agent_id)

        await self.db.execute(
            delete(OrchestratorAgent).where(OrchestratorAgent.id == agent_id)
        )
        await self.db.commit()

        logger.info(f"Deleted agent: {agent_id}")
        return True

    async def execute_agent(
        self,
        agent_id: int,
        request: ExecutionRequest,
        user_id: Optional[UUID] = None,
    ) -> ExecutionResult:
        """
        Execute an agent with a message.

        Args:
            agent_id: Agent ID
            request: Execution request
            user_id: User ID

        Returns:
            ExecutionResult
        """
        agent = await self.get_agent(agent_id)

        if not agent.is_active:
            raise OrchestratorError("Agent is not active")

        # Build agent config dict
        agent_config = {
            "id": agent.id,
            "name": agent.name,
            "system_prompt": agent.system_prompt,
            "goal": agent.goal,
            "identity_guidance": agent.identity_guidance,
            "llm_provider": agent.llm_provider,
            "model_name": agent.model_name,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "tools": agent.tools,
            "permissions": agent.permissions,
            "config": agent.config,
        }

        # Execute
        result = await self.orchestrator.run(
            agent_config=agent_config,
            message=request.message,
            thread_id=str(request.thread_id) if request.thread_id else None,
            metadata=request.metadata,
        )

        # Create execution record
        execution = AgentExecution(
            agent_id=agent_id,
            conversation_id=request.conversation_id,
            user_id=user_id,
            input_message=request.message,
            output_message=result.response,
            tool_calls=[{"tool": tc.get("name", ""), "args": tc.get("args", {})} for tc in result.tool_calls],
            tokens_input=result.tokens_input,
            tokens_output=result.tokens_output,
            tokens_total=result.tokens_total,
            duration_ms=result.duration_ms,
            status="completed",
        )

        self.db.add(execution)
        await self.db.commit()

        return result

    async def get_conversations(
        self,
        agent_id: int,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get conversations for an agent.

        Args:
            agent_id: Agent ID
            page: Page number
            page_size: Items per page
            user_id: Filter by user

        Returns:
            Dict with conversations and pagination
        """
        conditions = [OrchestratorConversation.agent_id == agent_id]
        if user_id:
            conditions.append(OrchestratorConversation.user_id == user_id)

        query = (
            select(OrchestratorConversation)
            .where(and_(*conditions))
            .order_by(OrchestratorConversation.created_at.desc())
        )

        # Count
        count_result = await self.db.execute(
            select(OrchestratorConversation.id).where(and_(*conditions))
        )
        total = len(count_result.all())

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        conversations = result.scalars().all()

        return {
            "conversations": conversations,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_executions(
        self,
        agent_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Get executions for an agent.

        Args:
            agent_id: Agent ID
            page: Page number
            page_size: Items per page

        Returns:
            Dict with executions and pagination
        """
        query = (
            select(AgentExecution)
            .where(AgentExecution.agent_id == agent_id)
            .order_by(AgentExecution.created_at.desc())
        )

        # Count
        count_result = await self.db.execute(
            select(AgentExecution.id).where(AgentExecution.agent_id == agent_id)
        )
        total = len(count_result.all())

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        executions = result.scalars().all()

        return {
            "executions": executions,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
