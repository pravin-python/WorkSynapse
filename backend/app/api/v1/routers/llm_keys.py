"""
LLM Key Management API Router
=============================

API endpoints for managing LLM providers, API keys, and AI agents.
"""

from typing import List, Optional
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user.model import User
from app.models.llm.model import LLMKeyProvider, LLMApiKey, UserAIAgent
from app.schemas.llm import (
    LLMProviderResponse, LLMProviderWithKeyStatus,
    LLMApiKeyCreate, LLMApiKeyUpdate, LLMApiKeyResponse,
    AIAgentCreate, AIAgentUpdate, AIAgentResponse,
    AIAgentCreateCheck, AIAgentCreateCheckResponse,
    LLMKeyStats, AgentStats
)
from app.schemas.agent_builder import (
    AgentModelCreate, AgentModelUpdate, AgentModelResponse
)
from app.services.agent_builder_service import AgentBuilderService
from app.services.llm_key_service import LLMKeyService, LLMKeyServiceError


router = APIRouter()


# ============================================
# PROVIDERS
# ============================================

@router.get("/providers", response_model=List[LLMProviderWithKeyStatus])
async def list_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all LLM providers with user's key status.
    
    Shows whether the current user has API keys for each provider.
    """
    providers = await LLMKeyService.get_providers(db)
    
    result = []
    for provider in providers:
        # Get user's keys for this provider
        keys = await LLMKeyService.get_user_keys(
            db, current_user.id, provider_id=provider.id
        )
        
        result.append(LLMProviderWithKeyStatus(
            id=provider.id,
            name=provider.name,
            type=provider.type.value,
            display_name=provider.display_name,
            description=provider.description,
            base_url=provider.base_url,
            requires_api_key=provider.requires_api_key,
            icon=provider.icon,
            is_active=provider.is_active,
            config_schema=json.loads(provider.config_schema) if provider.config_schema else None,
            created_at=provider.created_at,
            has_api_key=len(keys) > 0,
            key_count=len(keys)
        ))
    
    return result


@router.get("/providers/{provider_id}", response_model=LLMProviderResponse)
async def get_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific provider."""
    provider = await LLMKeyService.get_provider(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.get("/providers/{provider_id}/models", response_model=List[AgentModelResponse])
async def list_provider_models(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List models for a specific provider."""
    # Ensure provider exists
    provider = await LLMKeyService.get_provider(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    models = await AgentBuilderService.get_models(db, provider_id=provider_id)
    return models


@router.post("/providers/seed")
async def seed_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Seed default LLM providers (admin only)."""
    if current_user.role.value not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    count = await LLMKeyService.seed_default_providers(db)
    return {"message": f"Seeded {count} providers", "count": count}


# ============================================
# API KEYS
# ============================================

@router.get("/keys", response_model=List[LLMApiKeyResponse])
async def list_api_keys(
    provider_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List user's API keys.
    
    Optionally filter by provider.
    Keys are shown with masked preview only - never raw values.
    """
    keys = await LLMKeyService.get_user_keys(
        db, current_user.id, provider_id=provider_id
    )
    
    return [
        LLMApiKeyResponse(
            id=key.id,
            provider_id=key.provider_id,
            provider_name=key.provider.display_name if key.provider else None,
            label=key.label,
            key_preview=key.key_preview,
            is_active=key.is_active,
            is_valid=key.is_valid,
            last_used_at=key.last_used_at,
            usage_count=key.usage_count,
            created_at=key.created_at
        )
        for key in keys
    ]


@router.post("/keys", response_model=LLMApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: LLMApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new API key.
    
    The key will be encrypted before storage.
    Validation is performed based on the provider's expected format.
    """
    try:
        key = await LLMKeyService.create_key(db, current_user.id, data)
        return LLMApiKeyResponse(
            id=key.id,
            provider_id=key.provider_id,
            provider_name=key.provider.display_name if key.provider else None,
            label=key.label,
            key_preview=key.key_preview,
            is_active=key.is_active,
            is_valid=key.is_valid,
            last_used_at=key.last_used_at,
            usage_count=key.usage_count,
            created_at=key.created_at
        )
    except LLMKeyServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/keys/{key_id}", response_model=LLMApiKeyResponse)
async def get_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific API key (masked)."""
    key = await LLMKeyService.get_key(db, key_id, current_user.id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return LLMApiKeyResponse(
        id=key.id,
        provider_id=key.provider_id,
        provider_name=key.provider.display_name if key.provider else None,
        label=key.label,
        key_preview=key.key_preview,
        is_active=key.is_active,
        is_valid=key.is_valid,
        last_used_at=key.last_used_at,
        usage_count=key.usage_count,
        created_at=key.created_at
    )


@router.patch("/keys/{key_id}", response_model=LLMApiKeyResponse)
async def update_api_key(
    key_id: int,
    data: LLMApiKeyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an API key."""
    try:
        key = await LLMKeyService.update_key(db, key_id, current_user.id, data)
        if not key:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return LLMApiKeyResponse(
            id=key.id,
            provider_id=key.provider_id,
            provider_name=key.provider.display_name if key.provider else None,
            label=key.label,
            key_preview=key.key_preview,
            is_active=key.is_active,
            is_valid=key.is_valid,
            last_used_at=key.last_used_at,
            usage_count=key.usage_count,
            created_at=key.created_at
        )
    except LLMKeyServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/keys/{key_id}")
async def delete_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an API key."""
    try:
        success = await LLMKeyService.delete_key(db, key_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="API key not found")
        return {"message": "API key deleted successfully"}
    except LLMKeyServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# AGENTS
# ============================================

@router.get("/agents", response_model=List[AIAgentResponse])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's AI agents."""
    agents = await LLMKeyService.get_user_agents(db, current_user.id)
    
    return [
        AIAgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            provider_id=agent.provider_id,
            provider_name=agent.provider.display_name if agent.provider else None,
            api_key_id=agent.api_key_id,
            key_preview=agent.api_key.key_preview if agent.api_key else None,
            model_name=agent.model_name,
            type=agent.agent_type.value,  # Changed from type to agent_type
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            system_prompt=agent.system_prompt,
            status=agent.status.value,
            is_public=agent.is_public,
            total_requests=agent.total_requests,
            total_tokens_used=agent.total_tokens_used,
            last_used_at=agent.last_used_at,
            created_at=agent.created_at
        )
        for agent in agents
    ]


@router.post("/agents/check", response_model=AIAgentCreateCheckResponse)
async def check_agent_creation(
    data: AIAgentCreateCheck,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if an agent can be created for a provider.
    
    Returns whether the user has API keys for the provider
    and lists available keys.
    """
    can_create, keys, message = await LLMKeyService.check_can_create_agent(
        db, current_user.id, data.provider_id
    )
    
    provider = await LLMKeyService.get_provider(db, data.provider_id)
    
    return AIAgentCreateCheckResponse(
        can_create=can_create,
        has_api_key=len(keys) > 0,
        provider_name=provider.display_name if provider else "Unknown",
        available_keys=[
            LLMApiKeyResponse(
                id=key.id,
                provider_id=key.provider_id,
                provider_name=key.provider.display_name if key.provider else None,
                label=key.label,
                key_preview=key.key_preview,
                is_active=key.is_active,
                is_valid=key.is_valid,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
                created_at=key.created_at
            )
            for key in keys
        ],
        message=message
    )


@router.post("/agents", response_model=AIAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AIAgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new AI agent.
    
    Requires valid API key for the selected provider.
    """
    try:
        agent = await LLMKeyService.create_agent(db, current_user.id, data)
        return AIAgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            provider_id=agent.provider_id,
            provider_name=agent.provider.display_name if agent.provider else None,
            api_key_id=agent.api_key_id,
            key_preview=agent.api_key.key_preview if agent.api_key else None,
            model_name=agent.model_name,
            type=agent.agent_type.value,  # Changed from type to agent_type
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            system_prompt=agent.system_prompt,
            status=agent.status.value,
            is_public=agent.is_public,
            total_requests=agent.total_requests,
            total_tokens_used=agent.total_tokens_used,
            last_used_at=agent.last_used_at,
            created_at=agent.created_at
        )
    except LLMKeyServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/agents/{agent_id}", response_model=AIAgentResponse)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific agent."""
    agent = await LLMKeyService.get_agent(db, agent_id, current_user.id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AIAgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        provider_id=agent.provider_id,
        provider_name=agent.provider.display_name if agent.provider else None,
        api_key_id=agent.api_key_id,
        key_preview=agent.api_key.key_preview if agent.api_key else None,
        model_name=agent.model_name,
        type=agent.agent_type.value,  # Changed from type to agent_type
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
        system_prompt=agent.system_prompt,
        status=agent.status.value,
        is_public=agent.is_public,
        total_requests=agent.total_requests,
        total_tokens_used=agent.total_tokens_used,
        last_used_at=agent.last_used_at,
        created_at=agent.created_at
    )


@router.patch("/agents/{agent_id}", response_model=AIAgentResponse)
async def update_agent(
    agent_id: int,
    data: AIAgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an agent."""
    try:
        agent = await LLMKeyService.update_agent(db, agent_id, current_user.id, data)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return AIAgentResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            provider_id=agent.provider_id,
            provider_name=agent.provider.display_name if agent.provider else None,
            api_key_id=agent.api_key_id,
            key_preview=agent.api_key.key_preview if agent.api_key else None,
            model_name=agent.model_name,
            type=agent.agent_type.value,  # Changed from type to agent_type
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            system_prompt=agent.system_prompt,
            status=agent.status.value,
            is_public=agent.is_public,
            total_requests=agent.total_requests,
            total_tokens_used=agent.total_tokens_used,
            last_used_at=agent.last_used_at,
            created_at=agent.created_at
        )
    except LLMKeyServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
