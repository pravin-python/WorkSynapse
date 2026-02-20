"""
Agent Orchestrator API Routes
=============================

FastAPI routes for the agent orchestrator.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.database.session import get_db
from app.agents.orchestrator.models import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentListResponse,
    ExecutionRequest,
    ExecutionResponse,
    ConversationResponse,
    LLMProviderEnum,
)
from app.agents.orchestrator.service import AgentService
from app.agents.orchestrator.orchestrator import get_orchestrator
from app.agents.orchestrator.exceptions import (
    AgentNotFoundError,
    OrchestratorError,
    PromptInjectionError,
    RateLimitExceededError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Agent CRUD Endpoints
# ============================================================================


@router.post(
    "/",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
)
async def create_agent(
    data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_user),  # Add auth dependency
) -> AgentResponse:
    """
    Create a new AI agent with custom configuration.

    - **name**: Agent display name
    - **system_prompt**: Core behavior instructions
    - **llm_provider**: LLM provider (openai, ollama, gemini, claude, huggingface)
    - **tools**: List of tools the agent can use
    - **permissions**: Agent permissions configuration
    """
    try:
        service = AgentService(db)
        agent = await service.create_agent(data)

        return AgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            system_prompt=agent.system_prompt,
            goal=agent.goal,
            identity_guidance=agent.identity_guidance,
            llm_provider=LLMProviderEnum(agent.llm_provider),
            model_name=agent.model_name,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            tools=agent.tools,
            memory_type=agent.memory_type,
            permissions=agent.permissions,
            is_active=agent.is_active,
            is_public=agent.is_public,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    except Exception as e:
        logger.error(f"Create agent error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/",
    response_model=AgentListResponse,
    summary="List all agents",
)
async def list_agents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_public: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> AgentListResponse:
    """
    List all available agents with pagination.
    """
    try:
        service = AgentService(db)
        result = await service.list_agents(
            page=page,
            page_size=page_size,
            include_public=include_public,
        )

        agents = [
            AgentResponse(
                id=agent.id,
                name=agent.name,
                description=agent.description,
                system_prompt=agent.system_prompt[:200] + "..." if len(agent.system_prompt) > 200 else agent.system_prompt,
                goal=agent.goal,
                identity_guidance=agent.identity_guidance,
                llm_provider=LLMProviderEnum(agent.llm_provider),
                model_name=agent.model_name,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
                tools=agent.tools,
                memory_type=agent.memory_type,
                permissions=agent.permissions,
                is_active=agent.is_active,
                is_public=agent.is_public,
                created_at=agent.created_at,
                updated_at=agent.updated_at,
            )
            for agent in result["agents"]
        ]

        return AgentListResponse(
            agents=agents,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            has_more=result["has_more"],
        )

    except Exception as e:
        logger.error(f"List agents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Get agent by ID",
)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """
    Get detailed information about a specific agent.
    """
    try:
        service = AgentService(db)
        agent = await service.get_agent(agent_id)

        return AgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            system_prompt=agent.system_prompt,
            goal=agent.goal,
            identity_guidance=agent.identity_guidance,
            llm_provider=LLMProviderEnum(agent.llm_provider),
            model_name=agent.model_name,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            tools=agent.tools,
            memory_type=agent.memory_type,
            permissions=agent.permissions,
            is_active=agent.is_active,
            is_public=agent.is_public,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
    except Exception as e:
        logger.error(f"Get agent error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Update an agent",
)
async def update_agent(
    agent_id: int,
    data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
) -> AgentResponse:
    """
    Update an existing agent's configuration.
    """
    try:
        service = AgentService(db)
        agent = await service.update_agent(agent_id, data)

        return AgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            system_prompt=agent.system_prompt,
            goal=agent.goal,
            identity_guidance=agent.identity_guidance,
            llm_provider=LLMProviderEnum(agent.llm_provider),
            model_name=agent.model_name,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            tools=agent.tools,
            memory_type=agent.memory_type,
            permissions=agent.permissions,
            is_active=agent.is_active,
            is_public=agent.is_public,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
    except Exception as e:
        logger.error(f"Update agent error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an agent",
)
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an agent and all associated data.
    """
    try:
        service = AgentService(db)
        await service.delete_agent(agent_id)

    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
    except Exception as e:
        logger.error(f"Delete agent error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================================
# Agent Execution Endpoints
# ============================================================================


@router.post(
    "/{agent_id}/execute",
    response_model=ExecutionResponse,
    summary="Execute an agent",
)
async def execute_agent(
    agent_id: int,
    request: ExecutionRequest,
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    """
    Execute an agent with a message.

    Returns the agent's response along with execution metrics.
    """
    try:
        service = AgentService(db)
        result = await service.execute_agent(agent_id, request)

        return ExecutionResponse(
            response=result.response,
            thread_id=UUID(result.thread_id) if result.thread_id else None,
            tool_calls=[
                {"name": tc.get("name", ""), "arguments": tc.get("args", {})}
                for tc in result.tool_calls
            ],
            tokens_input=result.tokens_input,
            tokens_output=result.tokens_output,
            tokens_total=result.tokens_total,
            duration_ms=result.duration_ms,
        )

    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
    except PromptInjectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt injection detected",
        )
    except RateLimitExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Execute agent error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/{agent_id}/stream",
    summary="Stream agent response",
)
async def stream_agent(
    agent_id: int,
    request: ExecutionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Stream an agent's response in real-time.

    Uses Server-Sent Events (SSE) format.
    """
    try:
        service = AgentService(db)
        agent = await service.get_agent(agent_id)

        # Build agent config
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
        }

        orchestrator = get_orchestrator()

        async def generate():
            try:
                async for chunk in orchestrator.stream(
                    agent_config=agent_config,
                    message=request.message,
                    thread_id=str(request.thread_id) if request.thread_id else None,
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
    except Exception as e:
        logger.error(f"Stream agent error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================================
# Conversations & History Endpoints
# ============================================================================


@router.get(
    "/{agent_id}/conversations",
    summary="Get agent conversations",
)
async def get_conversations(
    agent_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get conversation history for an agent.
    """
    try:
        service = AgentService(db)
        result = await service.get_conversations(
            agent_id=agent_id,
            page=page,
            page_size=page_size,
        )

        return result

    except AgentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )
    except Exception as e:
        logger.error(f"Get conversations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{agent_id}/executions",
    summary="Get agent executions",
)
async def get_executions(
    agent_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get execution history for an agent.
    """
    try:
        service = AgentService(db)
        result = await service.get_executions(
            agent_id=agent_id,
            page=page,
            page_size=page_size,
        )

        return result

    except Exception as e:
        logger.error(f"Get executions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================================
# Provider & Tool Information Endpoints
# ============================================================================


@router.get(
    "/providers",
    summary="Get available LLM providers",
)
async def get_providers():
    """
    Get list of available LLM providers and their models.
    """
    orchestrator = get_orchestrator()
    return {
        "providers": orchestrator.get_available_providers(),
    }


@router.get(
    "/tools",
    summary="Get available tools",
)
async def get_tools():
    """
    Get list of available tools for agents.
    """
    orchestrator = get_orchestrator()
    return {
        "tools": orchestrator.get_available_tools(),
    }
