"""
WorkSynapse Custom Agent Builder Service
==========================================

Business logic for the Custom Agent Builder feature.
Handles CRUD operations, API key management, and validation.
"""

import re
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.agent_builder.model import (
    AgentModel, AgentApiKey, CustomAgent, AgentToolConfig,
    AgentConnection, AgentMCPServer, AgentModelProvider,
    CustomAgentStatus, AgentToolType, AgentConnectionType
)
from app.schemas.agent_builder import (
    AgentModelCreate, AgentModelUpdate,
    AgentApiKeyCreate, AgentApiKeyUpdate,
    CustomAgentCreate, CustomAgentUpdate,
    AgentToolConfigCreate, AgentToolConfigUpdate,
    AgentConnectionCreate, AgentConnectionUpdate,
    AgentMCPServerCreate, AgentMCPServerUpdate,
    AgentModelProviderEnum, CustomAgentStatusEnum
)
from app.core.encryption import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)


class AgentBuilderServiceError(Exception):
    """Base exception for agent builder service errors."""
    pass


class AgentBuilderService:
    """
    Service class for Custom Agent Builder operations.
    
    Handles all CRUD operations for agents, models, API keys,
    tools, connections, and MCP servers.
    """
    
    # ==========================================================================
    # AGENT MODELS
    # ==========================================================================
    
    @staticmethod
    async def get_models(
        db: AsyncSession,
        provider: Optional[AgentModelProviderEnum] = None,
        include_deprecated: bool = False
    ) -> List[AgentModel]:
        """Get all available AI models."""
        query = select(AgentModel).where(AgentModel.is_deleted == False)
        
        if provider:
            query = query.where(AgentModel.provider == AgentModelProvider(provider.value))
        
        if not include_deprecated:
            query = query.where(AgentModel.is_deprecated == False)
        
        query = query.where(AgentModel.is_active == True).order_by(AgentModel.display_name)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_model(db: AsyncSession, model_id: int) -> Optional[AgentModel]:
        """Get a specific model by ID."""
        query = select(AgentModel).where(
            AgentModel.id == model_id,
            AgentModel.is_deleted == False
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_model(db: AsyncSession, data: AgentModelCreate) -> AgentModel:
        """Create a new AI model."""
        model = AgentModel(
            name=data.name,
            display_name=data.display_name,
            provider=AgentModelProvider(data.provider.value),
            description=data.description,
            requires_api_key=data.requires_api_key,
            api_key_prefix=data.api_key_prefix,
            base_url=data.base_url,
            context_window=data.context_window,
            max_output_tokens=data.max_output_tokens,
            supports_vision=data.supports_vision,
            supports_tools=data.supports_tools,
            supports_streaming=data.supports_streaming,
            input_price_per_million=data.input_price_per_million,
            output_price_per_million=data.output_price_per_million,
        )
        db.add(model)
        await db.commit()
        await db.refresh(model)
        return model
    
    @staticmethod
    async def seed_default_models(db: AsyncSession) -> int:
        """Seed default AI models."""
        default_models = [
            # OpenAI Models
            {
                "name": "gpt-4o",
                "display_name": "GPT-4o",
                "provider": AgentModelProvider.OPENAI,
                "description": "Most capable GPT-4 model with vision support",
                "requires_api_key": True,
                "api_key_prefix": "sk-",
                "context_window": 128000,
                "max_output_tokens": 16384,
                "supports_vision": True,
                "supports_tools": True,
                "supports_streaming": True,
                "input_price_per_million": 2.5,
                "output_price_per_million": 10.0,
            },
            {
                "name": "gpt-4o-mini",
                "display_name": "GPT-4o Mini",
                "provider": AgentModelProvider.OPENAI,
                "description": "Fast and affordable GPT-4 variant",
                "requires_api_key": True,
                "api_key_prefix": "sk-",
                "context_window": 128000,
                "max_output_tokens": 16384,
                "supports_vision": True,
                "supports_tools": True,
                "supports_streaming": True,
                "input_price_per_million": 0.15,
                "output_price_per_million": 0.6,
            },
            {
                "name": "gpt-4-turbo",
                "display_name": "GPT-4 Turbo",
                "provider": AgentModelProvider.OPENAI,
                "description": "Enhanced GPT-4 with improved capabilities",
                "requires_api_key": True,
                "api_key_prefix": "sk-",
                "context_window": 128000,
                "max_output_tokens": 4096,
                "supports_vision": True,
                "supports_tools": True,
                "supports_streaming": True,
                "input_price_per_million": 10.0,
                "output_price_per_million": 30.0,
            },
            # Anthropic Models
            {
                "name": "claude-3-5-sonnet-20241022",
                "display_name": "Claude 3.5 Sonnet",
                "provider": AgentModelProvider.ANTHROPIC,
                "description": "Anthropic's most intelligent model",
                "requires_api_key": True,
                "api_key_prefix": "sk-ant-",
                "context_window": 200000,
                "max_output_tokens": 8192,
                "supports_vision": True,
                "supports_tools": True,
                "supports_streaming": True,
                "input_price_per_million": 3.0,
                "output_price_per_million": 15.0,
            },
            {
                "name": "claude-3-5-haiku-20241022",
                "display_name": "Claude 3.5 Haiku",
                "provider": AgentModelProvider.ANTHROPIC,
                "description": "Fast and cost-effective Claude model",
                "requires_api_key": True,
                "api_key_prefix": "sk-ant-",
                "context_window": 200000,
                "max_output_tokens": 8192,
                "supports_vision": True,
                "supports_tools": True,
                "supports_streaming": True,
                "input_price_per_million": 0.8,
                "output_price_per_million": 4.0,
            },
            # Google Models
            {
                "name": "gemini-2.0-flash-exp",
                "display_name": "Gemini 2.0 Flash",
                "provider": AgentModelProvider.GEMINI,
                "description": "Google's latest multimodal model",
                "requires_api_key": True,
                "api_key_prefix": None,
                "context_window": 1000000,
                "max_output_tokens": 8192,
                "supports_vision": True,
                "supports_tools": True,
                "supports_streaming": True,
                "input_price_per_million": 0.0,  # Currently free
                "output_price_per_million": 0.0,
            },
            {
                "name": "gemini-1.5-pro",
                "display_name": "Gemini 1.5 Pro",
                "provider": AgentModelProvider.GEMINI,
                "description": "Powerful multimodal model",
                "requires_api_key": True,
                "api_key_prefix": None,
                "context_window": 2000000,
                "max_output_tokens": 8192,
                "supports_vision": True,
                "supports_tools": True,
                "supports_streaming": True,
                "input_price_per_million": 1.25,
                "output_price_per_million": 5.0,
            },
            # Ollama (Local)
            {
                "name": "llama3.2",
                "display_name": "Llama 3.2 (Local)",
                "provider": AgentModelProvider.OLLAMA,
                "description": "Meta's latest open-source model",
                "requires_api_key": False,
                "api_key_prefix": None,
                "base_url": "http://localhost:11434",
                "context_window": 128000,
                "max_output_tokens": 4096,
                "supports_vision": False,
                "supports_tools": True,
                "supports_streaming": True,
                "input_price_per_million": 0.0,
                "output_price_per_million": 0.0,
            },
        ]
        
        count = 0
        for model_data in default_models:
            # Check if exists
            existing = await db.execute(
                select(AgentModel).where(AgentModel.name == model_data["name"])
            )
            if existing.scalar_one_or_none():
                continue
            
            model = AgentModel(**model_data)
            db.add(model)
            count += 1
        
        await db.commit()
        return count
    
    # ==========================================================================
    # API KEYS
    # ==========================================================================
    
    @staticmethod
    async def get_user_api_keys(
        db: AsyncSession,
        user_id: int,
        provider: Optional[AgentModelProviderEnum] = None
    ) -> List[AgentApiKey]:
        """Get all API keys for a user."""
        query = select(AgentApiKey).where(
            AgentApiKey.user_id == user_id,
            AgentApiKey.is_deleted == False
        )
        
        if provider:
            query = query.where(AgentApiKey.provider == AgentModelProvider(provider.value))
        
        query = query.order_by(AgentApiKey.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_api_key(
        db: AsyncSession,
        key_id: int,
        user_id: int
    ) -> Optional[AgentApiKey]:
        """Get a specific API key."""
        query = select(AgentApiKey).where(
            AgentApiKey.id == key_id,
            AgentApiKey.user_id == user_id,
            AgentApiKey.is_deleted == False
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        user_id: int,
        data: AgentApiKeyCreate
    ) -> AgentApiKey:
        """Create a new API key (encrypted)."""
        # Create masked preview
        key = data.api_key
        if len(key) > 8:
            key_preview = f"{key[:4]}...{key[-4:]}"
        else:
            key_preview = f"{key[:2]}...{key[-2:]}"
        
        # Encrypt the key
        encrypted_key = encrypt_value(key)
        
        api_key = AgentApiKey(
            user_id=user_id,
            provider=AgentModelProvider(data.provider.value),
            label=data.label,
            encrypted_key=encrypted_key,
            key_preview=key_preview,
        )
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        return api_key
    
    @staticmethod
    async def update_api_key(
        db: AsyncSession,
        key_id: int,
        user_id: int,
        data: AgentApiKeyUpdate
    ) -> Optional[AgentApiKey]:
        """Update an API key."""
        api_key = await AgentBuilderService.get_api_key(db, key_id, user_id)
        if not api_key:
            return None
        
        if data.label is not None:
            api_key.label = data.label
        if data.is_active is not None:
            api_key.is_active = data.is_active
        if data.api_key:
            # Re-encrypt new key
            key = data.api_key
            if len(key) > 8:
                api_key.key_preview = f"{key[:4]}...{key[-4:]}"
            else:
                api_key.key_preview = f"{key[:2]}...{key[-2:]}"
            api_key.encrypted_key = encrypt_value(key)
            api_key.is_valid = True
            api_key.last_validated_at = None
        
        await db.commit()
        await db.refresh(api_key)
        return api_key
    
    @staticmethod
    async def delete_api_key(
        db: AsyncSession,
        key_id: int,
        user_id: int
    ) -> bool:
        """Delete an API key (soft delete)."""
        api_key = await AgentBuilderService.get_api_key(db, key_id, user_id)
        if not api_key:
            return False
        
        # Check if key is being used by any agents
        agents_using = await db.execute(
            select(func.count(CustomAgent.id)).where(
                CustomAgent.api_key_id == key_id,
                CustomAgent.is_deleted == False
            )
        )
        if agents_using.scalar() > 0:
            raise AgentBuilderServiceError(
                "Cannot delete API key that is being used by agents"
            )
        
        api_key.soft_delete()
        await db.commit()
        return True
    
    @staticmethod
    async def check_api_key_exists(
        db: AsyncSession,
        user_id: int,
        provider: AgentModelProviderEnum
    ) -> Tuple[bool, List[AgentApiKey]]:
        """Check if user has API key for provider."""
        keys = await AgentBuilderService.get_user_api_keys(db, user_id, provider)
        active_keys = [k for k in keys if k.is_active and k.is_valid]
        return len(active_keys) > 0, active_keys
    
    # ==========================================================================
    # CUSTOM AGENTS
    # ==========================================================================
    
    @staticmethod
    def _generate_slug(name: str) -> str:
        """Generate a URL-safe slug from name."""
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        # Add unique suffix
        slug = f"{slug}-{uuid.uuid4().hex[:8]}"
        return slug
    
    @staticmethod
    async def get_agents(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CustomAgentStatusEnum] = None,
        include_public: bool = True
    ) -> Dict[str, Any]:
        """Get paginated list of agents for a user."""
        # Base query
        conditions = [CustomAgent.is_deleted == False]
        
        if include_public:
            conditions.append(
                or_(
                    CustomAgent.created_by_user_id == user_id,
                    CustomAgent.is_public == True
                )
            )
        else:
            conditions.append(CustomAgent.created_by_user_id == user_id)
        
        if status:
            conditions.append(CustomAgent.status == CustomAgentStatus(status.value))
        
        # Count total
        count_query = select(func.count(CustomAgent.id)).where(and_(*conditions))
        total = (await db.execute(count_query)).scalar()
        
        # Get agents with model info
        query = (
            select(CustomAgent)
            .options(
                joinedload(CustomAgent.model),
                joinedload(CustomAgent.api_key)
            )
            .where(and_(*conditions))
            .order_by(CustomAgent.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        
        result = await db.execute(query)
        agents = list(result.unique().scalars().all())
        
        return {
            "agents": agents,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total
        }
    
    @staticmethod
    async def get_agent(
        db: AsyncSession,
        agent_id: int,
        user_id: int
    ) -> Optional[CustomAgent]:
        """Get a specific agent with all related data."""
        query = (
            select(CustomAgent)
            .options(
                joinedload(CustomAgent.model),
                joinedload(CustomAgent.api_key),
                selectinload(CustomAgent.tools),
                selectinload(CustomAgent.connections),
                selectinload(CustomAgent.mcp_servers)
            )
            .where(
                CustomAgent.id == agent_id,
                CustomAgent.is_deleted == False,
                or_(
                    CustomAgent.created_by_user_id == user_id,
                    CustomAgent.is_public == True
                )
            )
        )
        
        result = await db.execute(query)
        return result.unique().scalar_one_or_none()
    
    @staticmethod
    async def get_agent_by_slug(
        db: AsyncSession,
        slug: str,
        user_id: int
    ) -> Optional[CustomAgent]:
        """Get agent by slug."""
        query = (
            select(CustomAgent)
            .options(
                joinedload(CustomAgent.model),
                joinedload(CustomAgent.api_key),
                selectinload(CustomAgent.tools),
                selectinload(CustomAgent.connections),
                selectinload(CustomAgent.mcp_servers)
            )
            .where(
                CustomAgent.slug == slug,
                CustomAgent.is_deleted == False,
                or_(
                    CustomAgent.created_by_user_id == user_id,
                    CustomAgent.is_public == True
                )
            )
        )
        
        result = await db.execute(query)
        return result.unique().scalar_one_or_none()
    
    @staticmethod
    async def create_agent(
        db: AsyncSession,
        user_id: int,
        data: CustomAgentCreate
    ) -> CustomAgent:
        """Create a new custom agent."""
        # Verify model exists
        model = await AgentBuilderService.get_model(db, data.model_id)
        if not model:
            raise AgentBuilderServiceError("Model not found")
        
        # Check API key if required
        if model.requires_api_key:
            if not data.api_key_id:
                raise AgentBuilderServiceError(
                    f"API key is required for {model.display_name}"
                )
            api_key = await AgentBuilderService.get_api_key(db, data.api_key_id, user_id)
            if not api_key:
                raise AgentBuilderServiceError("API key not found")
            if api_key.provider != model.provider:
                raise AgentBuilderServiceError(
                    f"API key provider ({api_key.provider.value}) does not match model provider ({model.provider.value})"
                )
        
        # Check for duplicate name
        existing = await db.execute(
            select(CustomAgent).where(
                CustomAgent.name == data.name,
                CustomAgent.created_by_user_id == user_id,
                CustomAgent.is_deleted == False
            )
        )
        if existing.scalar_one_or_none():
            raise AgentBuilderServiceError("An agent with this name already exists")
        
        # Create agent
        agent = CustomAgent(
            name=data.name,
            description=data.description,
            slug=AgentBuilderService._generate_slug(data.name),
            model_id=data.model_id,
            api_key_id=data.api_key_id,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            top_p=data.top_p,
            frequency_penalty=data.frequency_penalty,
            presence_penalty=data.presence_penalty,
            system_prompt=data.system_prompt,
            goal_prompt=data.goal_prompt,
            service_prompt=data.service_prompt,
            is_public=data.is_public,
            avatar_url=data.avatar_url,
            color=data.color,
            icon=data.icon,
            status=CustomAgentStatus.DRAFT,
            created_by_user_id=user_id,
            updated_by_user_id=user_id,
        )
        db.add(agent)
        await db.flush()  # Get the agent ID
        
        # Add tools
        if data.tools:
            for tool_data in data.tools:
                tool = AgentToolConfig(
                    agent_id=agent.id,
                    tool_type=AgentToolType(tool_data.tool_type.value),
                    tool_name=tool_data.tool_name,
                    display_name=tool_data.display_name,
                    description=tool_data.description,
                    config_json=tool_data.config_json,
                    is_enabled=tool_data.is_enabled,
                )
                db.add(tool)
        
        # Add connections
        if data.connections:
            for conn_data in data.connections:
                conn = AgentConnection(
                    agent_id=agent.id,
                    connection_type=AgentConnectionType(conn_data.connection_type.value),
                    name=conn_data.name,
                    display_name=conn_data.display_name,
                    description=conn_data.description,
                    config_json=conn_data.config_json,
                    created_by_user_id=user_id,
                )
                db.add(conn)
        
        # Add MCP servers
        if data.mcp_servers:
            for mcp_data in data.mcp_servers:
                mcp = AgentMCPServer(
                    agent_id=agent.id,
                    server_name=mcp_data.server_name,
                    server_url=mcp_data.server_url,
                    description=mcp_data.description,
                    config_json=mcp_data.config_json,
                    transport_type=mcp_data.transport_type,
                    requires_auth=mcp_data.requires_auth,
                    auth_type=mcp_data.auth_type,
                )
                if mcp_data.auth_credentials:
                    mcp.encrypted_auth = encrypt_value(mcp_data.auth_credentials)
                db.add(mcp)
        
        await db.commit()
        
        # Reload with relationships
        return await AgentBuilderService.get_agent(db, agent.id, user_id)
    
    @staticmethod
    async def update_agent(
        db: AsyncSession,
        agent_id: int,
        user_id: int,
        data: CustomAgentUpdate
    ) -> Optional[CustomAgent]:
        """Update a custom agent."""
        agent = await AgentBuilderService.get_agent(db, agent_id, user_id)
        if not agent:
            return None
        
        # Only creator can update
        if agent.created_by_user_id != user_id:
            raise AgentBuilderServiceError("Only the creator can update this agent")
        
        # Update fields
        update_fields = [
            "name", "description", "temperature", "max_tokens", "top_p",
            "frequency_penalty", "presence_penalty", "system_prompt",
            "goal_prompt", "service_prompt", "is_public", "avatar_url",
            "color", "icon"
        ]
        
        for field in update_fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(agent, field, value)
        
        # Handle model change
        if data.model_id and data.model_id != agent.model_id:
            model = await AgentBuilderService.get_model(db, data.model_id)
            if not model:
                raise AgentBuilderServiceError("Model not found")
            agent.model_id = data.model_id
            
            # May need to clear API key if provider changed
            if agent.api_key and agent.api_key.provider != model.provider:
                agent.api_key_id = None
        
        # Handle API key change
        if data.api_key_id is not None:
            if data.api_key_id == 0:
                agent.api_key_id = None
            else:
                api_key = await AgentBuilderService.get_api_key(db, data.api_key_id, user_id)
                if not api_key:
                    raise AgentBuilderServiceError("API key not found")
                agent.api_key_id = data.api_key_id
        
        # Handle status change
        if data.status:
            agent.status = CustomAgentStatus(data.status.value)
        
        agent.version += 1
        agent.updated_by_user_id = user_id
        
        await db.commit()
        return await AgentBuilderService.get_agent(db, agent_id, user_id)
    
    @staticmethod
    async def delete_agent(
        db: AsyncSession,
        agent_id: int,
        user_id: int
    ) -> bool:
        """Delete an agent (soft delete)."""
        agent = await AgentBuilderService.get_agent(db, agent_id, user_id)
        if not agent:
            return False
        
        if agent.created_by_user_id != user_id:
            raise AgentBuilderServiceError("Only the creator can delete this agent")
        
        agent.soft_delete()
        await db.commit()
        return True
    
    @staticmethod
    async def activate_agent(
        db: AsyncSession,
        agent_id: int,
        user_id: int
    ) -> Optional[CustomAgent]:
        """Activate an agent (change status to active)."""
        agent = await AgentBuilderService.get_agent(db, agent_id, user_id)
        if not agent:
            return None
        
        if agent.created_by_user_id != user_id:
            raise AgentBuilderServiceError("Only the creator can activate this agent")
        
        # Validate agent has required configuration
        errors = []
        
        if not agent.system_prompt:
            errors.append("System prompt is required")
        
        if agent.model.requires_api_key and not agent.api_key_id:
            errors.append("API key is required for this model")
        
        if errors:
            raise AgentBuilderServiceError(f"Cannot activate: {', '.join(errors)}")
        
        agent.status = CustomAgentStatus.ACTIVE
        await db.commit()
        return agent
    
    # ==========================================================================
    # AGENT TOOLS
    # ==========================================================================
    
    @staticmethod
    async def add_tool(
        db: AsyncSession,
        agent_id: int,
        user_id: int,
        data: AgentToolConfigCreate
    ) -> AgentToolConfig:
        """Add a tool to an agent."""
        agent = await AgentBuilderService.get_agent(db, agent_id, user_id)
        if not agent:
            raise AgentBuilderServiceError("Agent not found")
        if agent.created_by_user_id != user_id:
            raise AgentBuilderServiceError("Only the creator can modify this agent")
        
        # Check for duplicate tool
        for existing in agent.tools:
            if existing.tool_type == AgentToolType(data.tool_type.value):
                raise AgentBuilderServiceError(f"Tool {data.tool_type.value} already exists")
        
        tool = AgentToolConfig(
            agent_id=agent_id,
            tool_type=AgentToolType(data.tool_type.value),
            tool_name=data.tool_name,
            display_name=data.display_name,
            description=data.description,
            config_json=data.config_json,
            is_enabled=data.is_enabled,
        )
        db.add(tool)
        await db.commit()
        await db.refresh(tool)
        return tool
    
    @staticmethod
    async def update_tool(
        db: AsyncSession,
        tool_id: int,
        user_id: int,
        data: AgentToolConfigUpdate
    ) -> Optional[AgentToolConfig]:
        """Update a tool configuration."""
        query = (
            select(AgentToolConfig)
            .join(CustomAgent)
            .where(
                AgentToolConfig.id == tool_id,
                CustomAgent.created_by_user_id == user_id
            )
        )
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
        
        if not tool:
            return None
        
        if data.display_name is not None:
            tool.display_name = data.display_name
        if data.description is not None:
            tool.description = data.description
        if data.config_json is not None:
            tool.config_json = data.config_json
            tool.is_configured = True
        if data.is_enabled is not None:
            tool.is_enabled = data.is_enabled
        
        await db.commit()
        await db.refresh(tool)
        return tool
    
    @staticmethod
    async def remove_tool(
        db: AsyncSession,
        tool_id: int,
        user_id: int
    ) -> bool:
        """Remove a tool from an agent."""
        query = (
            select(AgentToolConfig)
            .join(CustomAgent)
            .where(
                AgentToolConfig.id == tool_id,
                CustomAgent.created_by_user_id == user_id
            )
        )
        result = await db.execute(query)
        tool = result.scalar_one_or_none()
        
        if not tool:
            return False
        
        await db.delete(tool)
        await db.commit()
        return True
    
    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """Get list of all available tools."""
        return [
            {
                "type": "github",
                "name": "github",
                "display_name": "GitHub",
                "description": "Interact with GitHub repositories, issues, and pull requests",
                "icon": "github",
                "requires_auth": True,
                "config_schema": {
                    "repository": {"type": "string", "description": "Repository in owner/repo format"},
                    "token": {"type": "string", "description": "Personal access token", "secret": True}
                }
            },
            {
                "type": "slack",
                "name": "slack",
                "display_name": "Slack",
                "description": "Send messages and interact with Slack workspaces",
                "icon": "slack",
                "requires_auth": True,
                "config_schema": {
                    "webhook_url": {"type": "string", "description": "Slack webhook URL", "secret": True},
                    "channel": {"type": "string", "description": "Default channel"}
                }
            },
            {
                "type": "telegram",
                "name": "telegram",
                "display_name": "Telegram",
                "description": "Send messages via Telegram bot",
                "icon": "telegram",
                "requires_auth": True,
                "config_schema": {
                    "bot_token": {"type": "string", "description": "Bot API token", "secret": True},
                    "chat_id": {"type": "string", "description": "Chat/group ID"}
                }
            },
            {
                "type": "filesystem",
                "name": "filesystem",
                "display_name": "File System",
                "description": "Read and write files in allowed directories",
                "icon": "folder",
                "requires_auth": False,
                "config_schema": {
                    "allowed_paths": {"type": "array", "description": "Allowed file paths"},
                    "read_only": {"type": "boolean", "description": "Read-only mode"}
                }
            },
            {
                "type": "web",
                "name": "web",
                "display_name": "Web Tools",
                "description": "Browse web, fetch URLs, and search",
                "icon": "globe",
                "requires_auth": False,
                "config_schema": {
                    "allowed_domains": {"type": "array", "description": "Allowed domains"},
                    "max_pages": {"type": "integer", "description": "Max pages per request"}
                }
            },
            {
                "type": "email",
                "name": "email",
                "display_name": "Email",
                "description": "Send and read emails",
                "icon": "mail",
                "requires_auth": True,
                "config_schema": {
                    "smtp_host": {"type": "string"},
                    "smtp_port": {"type": "integer"},
                    "username": {"type": "string"},
                    "password": {"type": "string", "secret": True}
                }
            },
            {
                "type": "database",
                "name": "database",
                "display_name": "Database",
                "description": "Query SQL databases",
                "icon": "database",
                "requires_auth": True,
                "config_schema": {
                    "connection_string": {"type": "string", "secret": True},
                    "read_only": {"type": "boolean"}
                }
            },
            {
                "type": "api",
                "name": "api",
                "display_name": "REST API",
                "description": "Make HTTP requests to external APIs",
                "icon": "api",
                "requires_auth": False,
                "config_schema": {
                    "base_url": {"type": "string"},
                    "headers": {"type": "object"},
                    "auth_header": {"type": "string", "secret": True}
                }
            },
        ]
    
    # ==========================================================================
    # MCP SERVERS
    # ==========================================================================
    
    @staticmethod
    async def add_mcp_server(
        db: AsyncSession,
        agent_id: int,
        user_id: int,
        data: AgentMCPServerCreate
    ) -> AgentMCPServer:
        """Add an MCP server to an agent."""
        agent = await AgentBuilderService.get_agent(db, agent_id, user_id)
        if not agent:
            raise AgentBuilderServiceError("Agent not found")
        if agent.created_by_user_id != user_id:
            raise AgentBuilderServiceError("Only the creator can modify this agent")
        
        mcp = AgentMCPServer(
            agent_id=agent_id,
            server_name=data.server_name,
            server_url=data.server_url,
            description=data.description,
            config_json=data.config_json,
            transport_type=data.transport_type,
            requires_auth=data.requires_auth,
            auth_type=data.auth_type,
        )
        if data.auth_credentials:
            mcp.encrypted_auth = encrypt_value(data.auth_credentials)
        
        db.add(mcp)
        await db.commit()
        await db.refresh(mcp)
        return mcp
    
    @staticmethod
    async def remove_mcp_server(
        db: AsyncSession,
        mcp_id: int,
        user_id: int
    ) -> bool:
        """Remove an MCP server from an agent."""
        query = (
            select(AgentMCPServer)
            .join(CustomAgent)
            .where(
                AgentMCPServer.id == mcp_id,
                CustomAgent.created_by_user_id == user_id
            )
        )
        result = await db.execute(query)
        mcp = result.scalar_one_or_none()
        
        if not mcp:
            return False
        
        await db.delete(mcp)
        await db.commit()
        return True
