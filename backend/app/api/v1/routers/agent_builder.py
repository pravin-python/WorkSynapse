"""
WorkSynapse Custom Agent Builder API Router
=============================================

API endpoints for the Custom Agent Builder feature.
Includes routes for agents, models, API keys, tools, connections, and MCP servers.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.api.deps import get_current_user, require_roles
from app.models.user.model import User, UserRole
from app.services.agent_builder_service import AgentBuilderService, AgentBuilderServiceError
from app.schemas.agent_builder import (
    # Model schemas
    AgentModelCreate, AgentModelUpdate, AgentModelResponse, AgentModelWithKeyStatus,
    # API Key schemas
    AgentApiKeyCreate, AgentApiKeyUpdate, AgentApiKeyResponse,
    ApiKeyValidationRequest, ApiKeyValidationResponse,
    # Agent schemas
    CustomAgentCreate, CustomAgentUpdate, CustomAgentResponse,
    CustomAgentDetailResponse, CustomAgentListResponse,
    # Tool schemas
    AgentToolConfigCreate, AgentToolConfigUpdate, AgentToolConfigResponse,
    # Connection schemas
    AgentConnectionCreate, AgentConnectionUpdate, AgentConnectionResponse,
    # MCP Server schemas
    AgentMCPServerCreate, AgentMCPServerUpdate, AgentMCPServerResponse,
    # Validation schemas
    AgentCreationCheck, AgentCreationCheckResponse,
    ValidateAgentRequest, ValidateAgentResponse,
    AvailableToolInfo, AvailableConnectionInfo,
    # Enums
    CustomAgentStatusEnum, AgentToolTypeEnum
)

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# AGENT MODELS
# =============================================================================

@router.get("/models", response_model=List[AgentModelWithKeyStatus])
async def list_models(
    provider_id: Optional[int] = None,
    include_deprecated: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all available AI models with user's API key status.
    
    Shows whether the current user has API keys for each model's provider.
    """
    models = await AgentBuilderService.get_models(db, provider_id, include_deprecated)
    
    result = []
    for model in models:
        # Get user's keys for this provider
        has_key, keys = await AgentBuilderService.check_api_key_exists(
            db, current_user.id, model.provider_id
        )
        
        result.append(AgentModelWithKeyStatus(
            id=model.id,
            name=model.name,
            display_name=model.display_name,
            provider_id=model.provider_id,
            provider=model.provider if getattr(model, "provider", None) else None,
            description=model.description,
            requires_api_key=model.requires_api_key,
            api_key_prefix=model.api_key_prefix,
            context_window=model.context_window,
            max_output_tokens=model.max_output_tokens,
            supports_vision=model.supports_vision,
            supports_tools=model.supports_tools,
            supports_streaming=model.supports_streaming,
            input_price_per_million=model.input_price_per_million,
            output_price_per_million=model.output_price_per_million,
            is_active=model.is_active,
            is_deprecated=model.is_deprecated,
            created_at=model.created_at,
            has_api_key=has_key,
            key_count=len(keys)
        ))
    
    return result


@router.get("/models/{model_id}", response_model=AgentModelResponse)
async def get_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific AI model."""
    model = await AgentBuilderService.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/models/seed")
async def seed_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Seed default AI models (admin only)."""
    count = await AgentBuilderService.seed_default_models(db)
    return {"message": f"Seeded {count} models", "count": count}


# =============================================================================
# API KEYS
# =============================================================================

@router.get("/api-keys", response_model=List[AgentApiKeyResponse])
async def list_api_keys(
    provider_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List user's API keys.
    
    Keys are shown with masked preview only - never raw values.
    """
    keys = await AgentBuilderService.get_user_api_keys(
        db, current_user.id, provider_id
    )
    
    return [
            AgentApiKeyResponse(
                id=key.id,
                provider_id=key.provider_id,
                provider_name=key.provider.display_name if getattr(key, "provider", None) else None,
                label=key.label,
                key_preview=key.key_preview,
                is_active=key.is_active,
                is_valid=key.is_valid,
                last_validated_at=key.last_validated_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
                created_at=key.created_at
            )
        for key in keys
    ]


@router.post("/api-keys", response_model=AgentApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: AgentApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new API key.
    
    The key will be encrypted before storage.
    """
    try:
        key = await AgentBuilderService.create_api_key(db, current_user.id, data)
        return AgentApiKeyResponse(
            id=key.id,
            provider_id=key.provider_id,
            provider_name=key.provider.display_name if getattr(key, "provider", None) else None,
            label=key.label,
            key_preview=key.key_preview,
            is_active=key.is_active,
            is_valid=key.is_valid,
            last_validated_at=key.last_validated_at,
            last_used_at=key.last_used_at,
            usage_count=key.usage_count,
            created_at=key.created_at
        )
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api-keys/{key_id}", response_model=AgentApiKeyResponse)
async def get_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific API key (masked)."""
    key = await AgentBuilderService.get_api_key(db, key_id, current_user.id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return AgentApiKeyResponse(
        id=key.id,
        provider_id=key.provider_id,
        provider_name=key.provider.display_name if getattr(key, "provider", None) else None,
        label=key.label,
        key_preview=key.key_preview,
        is_active=key.is_active,
        is_valid=key.is_valid,
        last_validated_at=key.last_validated_at,
        last_used_at=key.last_used_at,
        usage_count=key.usage_count,
        created_at=key.created_at
    )


@router.patch("/api-keys/{key_id}", response_model=AgentApiKeyResponse)
async def update_api_key(
    key_id: int,
    data: AgentApiKeyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an API key."""
    try:
        key = await AgentBuilderService.update_api_key(db, key_id, current_user.id, data)
        if not key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return AgentApiKeyResponse(
            id=key.id,
            provider_id=key.provider_id,
            provider_name=key.provider.display_name if getattr(key, "provider", None) else None,
            label=key.label,
            key_preview=key.key_preview,
            is_active=key.is_active,
            is_valid=key.is_valid,
            last_validated_at=key.last_validated_at,
            last_used_at=key.last_used_at,
            usage_count=key.usage_count,
            created_at=key.created_at
        )
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an API key."""
    try:
        success = await AgentBuilderService.delete_api_key(db, key_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        return {"message": "API key deleted successfully"}
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api-keys/check")
async def check_api_key_exists(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if user has API key for a provider."""
    has_key, keys = await AgentBuilderService.check_api_key_exists(
        db, current_user.id, provider_id
    )
    return {
        "has_api_key": has_key,
        "key_count": len(keys),
        "keys": [
            {
                "id": k.id,
                "label": k.label,
                "key_preview": k.key_preview,
                "is_active": k.is_active
            }
            for k in keys
        ]
    }


# =============================================================================
# RESOURCES (Prompts, Knowledge, etc.)
# =============================================================================

@router.get("/prompt-templates", response_model=List[Dict[str, Any]])
async def list_prompt_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List available prompt templates."""
    return await AgentBuilderService.get_prompt_templates(db)


@router.get("/knowledge-sources", response_model=List[Dict[str, Any]])
async def list_knowledge_sources(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List available knowledge sources."""
    return await AgentBuilderService.get_knowledge_sources(db)


# =============================================================================
# CUSTOM AGENTS
# =============================================================================

@router.get("/agents", response_model=CustomAgentListResponse)
async def list_agents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[CustomAgentStatusEnum] = None,
    include_public: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's custom agents with pagination."""
    result = await AgentBuilderService.get_agents(
        db, current_user.id, page, page_size, status, include_public
    )
    
    agents = [
        CustomAgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            slug=agent.slug,
            model_id=agent.model_id,
            local_model_id=agent.local_model_id,
                model_name=agent.model.display_name if agent.model else (agent.local_model.name if agent.local_model else None),
                model_provider=agent.model.provider.display_name if agent.model and getattr(agent.model, "provider", None) else ("local" if agent.local_model else None),
            api_key_id=agent.api_key_id,
            api_key_preview=agent.api_key.key_preview if agent.api_key else None,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            top_p=agent.top_p,
            frequency_penalty=agent.frequency_penalty,
            presence_penalty=agent.presence_penalty,
            system_prompt=agent.system_prompt[:200] + "..." if len(agent.system_prompt) > 200 else agent.system_prompt,
            goal_prompt=agent.goal_prompt,
            service_prompt=agent.service_prompt,
            status=CustomAgentStatusEnum(agent.status.value),
            is_public=agent.is_public,
            total_sessions=agent.total_sessions,
            total_messages=agent.total_messages,
            total_tokens_used=agent.total_tokens_used,
            total_cost_usd=agent.total_cost_usd,
            last_used_at=agent.last_used_at,
            version=agent.version,
            avatar_url=agent.avatar_url,
            color=agent.color,
            icon=agent.icon,
            created_at=agent.created_at,
            updated_at=agent.updated_at
        )
        for agent in result["agents"]
    ]
    
    return CustomAgentListResponse(
        agents=agents,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        has_more=result["has_more"]
    )


@router.get("/agents/{agent_id}", response_model=CustomAgentDetailResponse)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a custom agent."""
    agent = await AgentBuilderService.get_agent(db, agent_id, current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return CustomAgentDetailResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        slug=agent.slug,
        model_id=agent.model_id,
        local_model_id=agent.local_model_id,
            model_name=agent.model.display_name if agent.model else (agent.local_model.name if agent.local_model else None),
            model_provider=agent.model.provider.display_name if agent.model and getattr(agent.model, "provider", None) else ("local" if agent.local_model else None),
        api_key_id=agent.api_key_id,
        api_key_preview=agent.api_key.key_preview if agent.api_key else None,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
        top_p=agent.top_p,
        frequency_penalty=agent.frequency_penalty,
        presence_penalty=agent.presence_penalty,
        system_prompt=agent.system_prompt,
        goal_prompt=agent.goal_prompt,
        service_prompt=agent.service_prompt,
        status=CustomAgentStatusEnum(agent.status.value),
        is_public=agent.is_public,
        total_sessions=agent.total_sessions,
        total_messages=agent.total_messages,
        total_tokens_used=agent.total_tokens_used,
        total_cost_usd=agent.total_cost_usd,
        last_used_at=agent.last_used_at,
        version=agent.version,
        avatar_url=agent.avatar_url,
        color=agent.color,
        icon=agent.icon,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        tools=[
            AgentToolConfigResponse(
                id=t.id,
                agent_id=t.agent_id,
                tool_type=AgentToolTypeEnum(t.tool_type.value),
                tool_name=t.tool_name,
                display_name=t.display_name,
                description=t.description,
                config_json=t.config_json,
                is_enabled=t.is_enabled,
                requires_auth=t.requires_auth,
                is_configured=t.is_configured,
                created_at=t.created_at,
                updated_at=t.updated_at
            )
            for t in agent.tools
        ],
        connections=[
            AgentConnectionResponse(
                id=c.id,
                agent_id=c.agent_id,
                connection_type=c.connection_type,
                name=c.name,
                display_name=c.display_name,
                description=c.description,
                config_json=c.config_json,
                is_active=c.is_active,
                is_connected=c.is_connected,
                last_connected_at=c.last_connected_at,
                last_error=c.last_error,
                created_at=c.created_at
            )
            for c in agent.connections
        ],
        mcp_servers=[
            AgentMCPServerResponse(
                id=m.id,
                agent_id=m.agent_id,
                server_name=m.server_name,
                server_url=m.server_url,
                description=m.description,
                config_json=m.config_json,
                transport_type=m.transport_type,
                requires_auth=m.requires_auth,
                is_enabled=m.is_enabled,
                is_connected=m.is_connected,
                last_health_check=m.last_health_check,
                last_error=m.last_error,
                available_tools=m.available_tools,
                available_resources=m.available_resources,
                created_at=m.created_at,
                updated_at=m.updated_at
            )
            for m in agent.mcp_servers
        ]
    )


@router.post("/agents", response_model=CustomAgentDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: CustomAgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.DEVELOPER]))
):
    """
    Create a new custom agent.
    
    Only Admin and Staff roles can create agents.
    Requires a valid API key for models that need one.
    """
    try:
        agent = await AgentBuilderService.create_agent(db, current_user.id, data)
        return await get_agent(agent.id, db, current_user)
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/agents/{agent_id}", response_model=CustomAgentDetailResponse)
async def update_agent(
    agent_id: int,
    data: CustomAgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a custom agent."""
    try:
        agent = await AgentBuilderService.update_agent(db, agent_id, current_user.id, data)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return await get_agent(agent_id, db, current_user)
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a custom agent."""
    try:
        success = await AgentBuilderService.delete_agent(db, agent_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"message": "Agent deleted successfully"}
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/{agent_id}/activate", response_model=CustomAgentResponse)
async def activate_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate an agent (change status to active)."""
    try:
        agent = await AgentBuilderService.activate_agent(db, agent_id, current_user.id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return CustomAgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            slug=agent.slug,
            model_id=agent.model_id,
            local_model_id=agent.local_model_id,
            model_name=agent.model.display_name if agent.model else (agent.local_model.name if agent.local_model else None),
            model_provider=agent.model.provider.display_name if agent.model and getattr(agent.model, "provider", None) else ("local" if agent.local_model else None),
            api_key_id=agent.api_key_id,
            api_key_preview=agent.api_key.key_preview if agent.api_key else None,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            top_p=agent.top_p,
            frequency_penalty=agent.frequency_penalty,
            presence_penalty=agent.presence_penalty,
            system_prompt=agent.system_prompt,
            goal_prompt=agent.goal_prompt,
            service_prompt=agent.service_prompt,
            status=CustomAgentStatusEnum(agent.status.value),
            is_public=agent.is_public,
            total_sessions=agent.total_sessions,
            total_messages=agent.total_messages,
            total_tokens_used=agent.total_tokens_used,
            total_cost_usd=agent.total_cost_usd,
            last_used_at=agent.last_used_at,
            version=agent.version,
            avatar_url=agent.avatar_url,
            color=agent.color,
            icon=agent.icon,
            created_at=agent.created_at,
            updated_at=agent.updated_at
        )
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agents/check-creation", response_model=AgentCreationCheckResponse)
async def check_agent_creation(
    data: AgentCreationCheck,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if an agent can be created with the specified model."""
    model = await AgentBuilderService.get_model(db, data.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    has_key, keys = await AgentBuilderService.check_api_key_exists(
        db, current_user.id, model.provider_id
    )
    
    can_create = not model.requires_api_key or has_key
    message = "Ready to create agent" if can_create else f"API key required for {model.display_name}"
    
    return AgentCreationCheckResponse(
        can_create=can_create,
        has_api_key=has_key,
        model_name=model.display_name,
        model_provider=model.provider.display_name if getattr(model, "provider", None) else None,
        requires_api_key=model.requires_api_key,
        available_keys=[
            AgentApiKeyResponse(
                id=k.id,
                provider_id=k.provider_id,
                provider_name=k.provider.display_name if getattr(k, "provider", None) else None,
                label=k.label,
                key_preview=k.key_preview,
                is_active=k.is_active,
                is_valid=k.is_valid,
                last_validated_at=k.last_validated_at,
                last_used_at=k.last_used_at,
                usage_count=k.usage_count,
                created_at=k.created_at
            )
            for k in keys
        ],
        message=message
    )


# =============================================================================
# AGENT TOOLS
# =============================================================================

@router.get("/tools/available", response_model=List[AvailableToolInfo])
async def get_available_tools():
    """Get list of all available tools for agents."""
    tools = AgentBuilderService.get_available_tools()
    return [
        AvailableToolInfo(
            type=AgentToolTypeEnum(t["type"]),
            name=t["name"],
            display_name=t["display_name"],
            description=t["description"],
            icon=t["icon"],
            requires_auth=t["requires_auth"],
            config_schema=t.get("config_schema")
        )
        for t in tools
    ]


@router.post("/agents/{agent_id}/tools", response_model=AgentToolConfigResponse, status_code=status.HTTP_201_CREATED)
async def add_tool_to_agent(
    agent_id: int,
    data: AgentToolConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a tool to an agent."""
    try:
        tool = await AgentBuilderService.add_tool(db, agent_id, current_user.id, data)
        return AgentToolConfigResponse(
            id=tool.id,
            agent_id=tool.agent_id,
            tool_type=AgentToolTypeEnum(tool.tool_type.value),
            tool_name=tool.tool_name,
            display_name=tool.display_name,
            description=tool.description,
            config_json=tool.config_json,
            is_enabled=tool.is_enabled,
            requires_auth=tool.requires_auth,
            is_configured=tool.is_configured,
            created_at=tool.created_at,
            updated_at=tool.updated_at
        )
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/agents/{agent_id}/tools/{tool_id}", response_model=AgentToolConfigResponse)
async def update_agent_tool(
    agent_id: int,
    tool_id: int,
    data: AgentToolConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a tool configuration."""
    try:
        tool = await AgentBuilderService.update_tool(db, tool_id, current_user.id, data)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return AgentToolConfigResponse(
            id=tool.id,
            agent_id=tool.agent_id,
            tool_type=AgentToolTypeEnum(tool.tool_type.value),
            tool_name=tool.tool_name,
            display_name=tool.display_name,
            description=tool.description,
            config_json=tool.config_json,
            is_enabled=tool.is_enabled,
            requires_auth=tool.requires_auth,
            is_configured=tool.is_configured,
            created_at=tool.created_at,
            updated_at=tool.updated_at
        )
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/agents/{agent_id}/tools/{tool_id}")
async def remove_tool_from_agent(
    agent_id: int,
    tool_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a tool from an agent."""
    try:
        success = await AgentBuilderService.remove_tool(db, tool_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Tool not found")
        return {"message": "Tool removed successfully"}
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# MCP SERVERS
# =============================================================================

@router.post("/agents/{agent_id}/mcp-servers", response_model=AgentMCPServerResponse, status_code=status.HTTP_201_CREATED)
async def add_mcp_server_to_agent(
    agent_id: int,
    data: AgentMCPServerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add an MCP server to an agent."""
    try:
        mcp = await AgentBuilderService.add_mcp_server(db, agent_id, current_user.id, data)
        return AgentMCPServerResponse(
            id=mcp.id,
            agent_id=mcp.agent_id,
            server_name=mcp.server_name,
            server_url=mcp.server_url,
            description=mcp.description,
            config_json=mcp.config_json,
            transport_type=mcp.transport_type,
            requires_auth=mcp.requires_auth,
            is_enabled=mcp.is_enabled,
            is_connected=mcp.is_connected,
            last_health_check=mcp.last_health_check,
            last_error=mcp.last_error,
            available_tools=mcp.available_tools,
            available_resources=mcp.available_resources,
            created_at=mcp.created_at,
            updated_at=mcp.updated_at
        )
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/agents/{agent_id}/mcp-servers/{mcp_id}")
async def remove_mcp_server_from_agent(
    agent_id: int,
    mcp_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove an MCP server from an agent."""
    try:
        success = await AgentBuilderService.remove_mcp_server(db, mcp_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="MCP server not found")
        return {"message": "MCP server removed successfully"}
    except AgentBuilderServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
