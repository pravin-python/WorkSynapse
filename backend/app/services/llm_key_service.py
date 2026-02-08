"""
LLM Key Management Service
==========================

Business logic for managing LLM providers, API keys, and agents.
"""

import json
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.llm.model import (
    LLMKeyProvider, LLMKeyProviderType,
    LLMApiKey, 
    UserAIAgent, UserAgentType, UserAgentStatus,
    UserAgentSession
)
from app.schemas.llm import (
    LLMProviderCreate, LLMProviderUpdate,
    LLMApiKeyCreate, LLMApiKeyUpdate,
    AIAgentCreate, AIAgentUpdate
)
from app.utils.encryption import (
    encrypt_api_key, 
    decrypt_api_key, 
    validate_api_key,
    mask_api_key,
    KeyEncryptionError
)


class LLMKeyServiceError(Exception):
    """Service-level error."""
    pass


class LLMKeyService:
    """Service for managing LLM API keys."""
    
    # ============================================
    # PROVIDERS
    # ============================================
    
    @staticmethod
    async def get_providers(
        db: AsyncSession,
        active_only: bool = True
    ) -> List[LLMKeyProvider]:
        """Get all LLM providers."""
        query = select(LLMKeyProvider)
        if active_only:
            query = query.where(LLMKeyProvider.is_active == True)
        query = query.order_by(LLMKeyProvider.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_provider(db: AsyncSession, provider_id: int) -> Optional[LLMKeyProvider]:
        """Get a provider by ID."""
        result = await db.execute(
            select(LLMKeyProvider).where(LLMKeyProvider.id == provider_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_provider_by_name(db: AsyncSession, name: str) -> Optional[LLMKeyProvider]:
        """Get a provider by name."""
        result = await db.execute(
            select(LLMKeyProvider).where(LLMKeyProvider.name == name.lower())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_provider(
        db: AsyncSession,
        data: LLMProviderCreate
    ) -> LLMKeyProvider:
        """Create a new provider."""
        provider = LLMKeyProvider(
            name=data.name.lower(),
            type=LLMKeyProviderType(data.type) if data.type else LLMKeyProviderType.CUSTOM,
            display_name=data.display_name,
            description=data.description,
            base_url=data.base_url,
            requires_api_key=data.requires_api_key,
            icon=data.icon,
            config_schema=json.dumps(data.config_schema) if data.config_schema else None
        )
        db.add(provider)
        await db.commit()
        await db.refresh(provider)
        return provider
    
    @staticmethod
    async def seed_default_providers(db: AsyncSession) -> int:
        """Seed default LLM providers and models if they don't exist."""
        # Import AgentModel here to avoid circular imports at module level if any
        from app.models.agent_builder.model import AgentModel
        
        default_providers = [
            {
                "name": "openai",
                "type": LLMKeyProviderType.OPENAI,
                "display_name": "OpenAI",
                "description": "GPT-4, GPT-3.5 and other OpenAI models",
                "icon": "openai",
                "models": [
                    {"name": "gpt-4o", "display_name": "GPT-4o", "context_window": 128000, "input_price": 5.0, "output_price": 15.0},
                    {"name": "gpt-4o-mini", "display_name": "GPT-4o Mini", "context_window": 128000, "input_price": 0.15, "output_price": 0.6},
                    {"name": "gpt-4-turbo", "display_name": "GPT-4 Turbo", "context_window": 128000, "input_price": 10.0, "output_price": 30.0},
                    {"name": "gpt-4", "display_name": "GPT-4", "context_window": 8192, "input_price": 30.0, "output_price": 60.0},
                    {"name": "gpt-3.5-turbo", "display_name": "GPT-3.5 Turbo", "context_window": 16385, "input_price": 0.5, "output_price": 1.5}
                ]
            },
            {
                "name": "anthropic",
                "type": LLMKeyProviderType.ANTHROPIC,
                "display_name": "Anthropic",
                "description": "Claude 3 family of models",
                "icon": "anthropic",
                "models": [
                    {"name": "claude-3-5-sonnet-latest", "display_name": "Claude 3.5 Sonnet", "context_window": 200000, "input_price": 3.0, "output_price": 15.0},
                    {"name": "claude-3-opus-latest", "display_name": "Claude 3 Opus", "context_window": 200000, "input_price": 15.0, "output_price": 75.0},
                    {"name": "claude-3-haiku-20240307", "display_name": "Claude 3 Haiku", "context_window": 200000, "input_price": 0.25, "output_price": 1.25}
                ]
            },
            {
                "name": "google",
                "type": LLMKeyProviderType.GOOGLE,
                "display_name": "Google AI",
                "description": "Gemini Pro and other Google models",
                "icon": "google",
                "models": [
                    {"name": "gemini-1.5-pro", "display_name": "Gemini 1.5 Pro", "context_window": 1048576, "input_price": 3.5, "output_price": 10.5},
                    {"name": "gemini-1.5-flash", "display_name": "Gemini 1.5 Flash", "context_window": 1048576, "input_price": 0.35, "output_price": 1.05},
                    {"name": "gemini-1.0-pro", "display_name": "Gemini 1.0 Pro", "context_window": 32000, "input_price": 0.5, "output_price": 1.5}
                ]
            },
            {
                "name": "huggingface",
                "type": LLMKeyProviderType.HUGGINGFACE,
                "display_name": "HuggingFace",
                "description": "Open source models via HuggingFace API",
                "icon": "huggingface",
                "models": [
                    {"name": "meta-llama/Llama-3.1-8B-Instruct", "display_name": "Llama 3.1 8B", "context_window": 8192},
                    {"name": "mistralai/Mistral-7B-Instruct-v0.3", "display_name": "Mistral 7B v0.3", "context_window": 32000}
                ]
            },
            {
                "name": "ollama",
                "type": LLMKeyProviderType.OLLAMA,
                "display_name": "Ollama (Local)",
                "description": "Run models locally with Ollama",
                "base_url": "http://localhost:11434",
                "requires_api_key": False,
                "icon": "server",
                "models": [
                    {"name": "llama3.1", "display_name": "Llama 3.1", "context_window": 128000},
                    {"name": "llama3", "display_name": "Llama 3", "context_window": 8192},
                    {"name": "mistral", "display_name": "Mistral", "context_window": 32000},
                    {"name": "phi3", "display_name": "Phi-3", "context_window": 128000}
                ]
            },
            {
                "name": "azure_openai",
                "type": LLMKeyProviderType.AZURE_OPENAI,
                "display_name": "Azure OpenAI",
                "description": "Enterprise-grade AI with Azure OpenAI Service",
                "icon": "azure_openai",
                "models": [
                    {"name": "azure-gpt-4", "display_name": "GPT-4 (Azure)", "context_window": 8192},
                    {"name": "azure-gpt-35-turbo", "display_name": "GPT-3.5 Turbo (Azure)", "context_window": 16385}
                ],
                "config_schema": {
                    "fields": [
                        {"name": "azure_endpoint", "type": "text", "label": "Endpoint URL", "required": True, "placeholder": "https://resource-name.openai.azure.com/"},
                        {"name": "deployment_name", "type": "text", "label": "Deployment Name", "required": True},
                        {"name": "api_version", "type": "text", "label": "API Version", "required": True, "default": "2023-05-15"}
                    ],
                    "help_link": "https://portal.azure.com"
                }
            },
            {
                "name": "aws_bedrock",
                "type": LLMKeyProviderType.AWS_BEDROCK,
                "display_name": "AWS Bedrock",
                "description": "Build generative AI applications with Amazon Bedrock",
                "icon": "aws_bedrock",
                "models": [
                    {"name": "anthropic.claude-3-sonnet-20240229-v1:0", "display_name": "Claude 3 Sonnet", "context_window": 200000, "input_price": 3.0, "output_price": 15.0},
                    {"name": "anthropic.claude-3-haiku-20240307-v1:0", "display_name": "Claude 3 Haiku", "context_window": 200000, "input_price": 0.25, "output_price": 1.25},
                    {"name": "amazon.titan-text-express-v1", "display_name": "Titan Text Express", "context_window": 8000}
                ],
                "config_schema": {
                    "fields": [
                        {"name": "aws_access_key_id", "type": "text", "label": "Access Key ID", "required": True},
                        {"name": "aws_secret_access_key", "type": "password", "label": "Secret Access Key", "required": True},
                        {"name": "region_name", "type": "text", "label": "Region", "required": True, "default": "us-east-1"}
                    ],
                    "help_link": "https://aws.amazon.com/bedrock",
                    "use_api_key_field": False
                }
            },
            {
                "name": "deepseek",
                "type": LLMKeyProviderType.DEEPSEEK,
                "display_name": "DeepSeek",
                "description": "DeepSeek open models",
                "base_url": "https://api.deepseek.com/v1",
                "icon": "deepseek",
                "models": [
                    {"name": "deepseek-chat", "display_name": "DeepSeek Chat", "context_window": 32000},
                    {"name": "deepseek-coder", "display_name": "DeepSeek Coder", "context_window": 32000}
                ],
                "help_link": "https://platform.deepseek.com"
            },
            {
                "name": "cohere",
                "type": LLMKeyProviderType.COHERE,
                "display_name": "Cohere",
                "description": "Command and other Cohere models",
                "icon": "cohere",
                "models": [
                    {"name": "command-r-plus", "display_name": "Command R+", "context_window": 128000},
                    {"name": "command-r", "display_name": "Command R", "context_window": 128000},
                    {"name": "command", "display_name": "Command", "context_window": 4096}
                ]
            },
            {
                "name": "groq",
                "type": LLMKeyProviderType.GROQ,
                "display_name": "Groq",
                "description": "Ultra-fast inference for open source models",
                "base_url": "https://api.groq.com/openai/v1",
                "icon": "groq",
                "models": [
                    {"name": "llama3-70b-8192", "display_name": "Llama 3 70B", "context_window": 8192, "input_price": 0.59, "output_price": 0.79},
                    {"name": "mixtral-8x7b-32768", "display_name": "Mixtral 8x7B", "context_window": 32768, "input_price": 0.24, "output_price": 0.24},
                    {"name": "gemma2-9b-it", "display_name": "Gemma 2 9B", "context_window": 8192, "input_price": 0.20, "output_price": 0.20}
                ],
                "help_link": "https://console.groq.com"
            },
        ]
        
        created = 0
        
        # Cache existing providers to minimize DB hits
        existing_providers = await LLMKeyService.get_providers(db, active_only=False)
        provider_map = {p.name: p for p in existing_providers}
        
        for pdata in default_providers:
            # 1. Create or Update Provider
            if pdata["name"] not in provider_map:
                provider = LLMKeyProvider(
                    name=pdata["name"],
                    type=pdata["type"],
                    display_name=pdata["display_name"],
                    description=pdata.get("description"),
                    base_url=pdata.get("base_url"),
                    requires_api_key=pdata.get("requires_api_key", True),
                    icon=pdata.get("icon"),
                    config_schema=json.dumps(pdata.get("config_schema")) if pdata.get("config_schema") else None
                )
                db.add(provider)
                await db.flush() # Flush to get ID
                provider_map[pdata["name"]] = provider
                created += 1
            else:
                provider = provider_map[pdata["name"]]
                # Update schema if changed
                new_schema = json.dumps(pdata.get("config_schema")) if pdata.get("config_schema") else None
                if provider.config_schema != new_schema:
                    provider.config_schema = new_schema

            # 2. Sync Models
            current_models_result = await db.execute(select(AgentModel).where(AgentModel.provider_id == provider.id))
            current_models = {m.name: m for m in current_models_result.scalars().all()}
            
            for mdata in pdata.get("models", []):
                if mdata["name"] not in current_models:
                    model = AgentModel(
                         name=mdata["name"],
                         display_name=mdata["display_name"],
                         provider_id=provider.id,
                         context_window=mdata.get("context_window", 4096),
                         input_price_per_million=mdata.get("input_price", 0.0),
                         output_price_per_million=mdata.get("output_price", 0.0),
                         is_active=True
                    )
                    db.add(model)
                else:
                    # Optional: Update pricing/specs if needed
                    existing_model = current_models[mdata["name"]]
                    if existing_model.input_price_per_million != mdata.get("input_price", 0.0):
                         existing_model.input_price_per_million = mdata.get("input_price", 0.0)
                         existing_model.output_price_per_million = mdata.get("output_price", 0.0)

        await db.commit()
        return created
    
    # ============================================
    # API KEYS
    # ============================================
    
    @staticmethod
    async def get_user_keys(
        db: AsyncSession,
        user_id: int,
        provider_id: Optional[int] = None,
        active_only: bool = True
    ) -> List[LLMApiKey]:
        """Get all API keys for a user."""
        query = select(LLMApiKey).options(
            selectinload(LLMApiKey.provider)
        ).where(LLMApiKey.user_id == user_id)
        
        if provider_id:
            query = query.where(LLMApiKey.provider_id == provider_id)
        if active_only:
            query = query.where(LLMApiKey.is_active == True)
        
        query = query.order_by(LLMApiKey.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_key(
        db: AsyncSession, 
        key_id: int,
        user_id: int
    ) -> Optional[LLMApiKey]:
        """Get a specific API key."""
        result = await db.execute(
            select(LLMApiKey)
            .options(selectinload(LLMApiKey.provider))
            .where(
                LLMApiKey.id == key_id,
                LLMApiKey.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_key(
        db: AsyncSession,
        user_id: int,
        data: LLMApiKeyCreate
    ) -> LLMApiKey:
        """Create a new encrypted API key."""
        # Validate provider exists
        provider = await LLMKeyService.get_provider(db, data.provider_id)
        if not provider:
            raise LLMKeyServiceError("Provider not found")
        
        # Check standard API key validation only if using standard field
        # Some providers like AWS might use custom fields instead
        use_standard_key = True
        if provider.config_schema:
            try:
                schema = json.loads(provider.config_schema)
                if schema.get("use_api_key_field") is False:
                    use_standard_key = False
            except:
                pass

        if use_standard_key:
            # Validate key format
            is_valid, error = validate_api_key(data.api_key, provider.name)
            if not is_valid:
                raise LLMKeyServiceError(f"Invalid API key format: {error}")
            
            # Encrypt the key
            try:
                encrypted = encrypt_api_key(data.api_key)
            except KeyEncryptionError as e:
                raise LLMKeyServiceError(f"Failed to encrypt key: {str(e)}")
            
            # Create masked preview
            preview = mask_api_key(data.api_key)
        else:
            # For providers not using standard key field (like AWS), we store a dummy/placeholder
            # The real credentials will be in extra_params
            encrypted = "stored_in_extra_params"
            preview = "config_based"

        # Create the key record
        api_key = LLMApiKey(
            provider_id=data.provider_id,
            user_id=user_id,
            label=data.label,
            encrypted_key=encrypted,
            key_preview=preview,
            extra_params=json.dumps(data.extra_params) if data.extra_params else None,
            is_active=True,
            is_valid=True
        )
        
        db.add(api_key)
        try:
            await db.commit()
            await db.refresh(api_key)
        except IntegrityError:
            await db.rollback()
            raise LLMKeyServiceError(
                f"An API key with the label '{data.label}' already exists for this provider."
            )
        
        # Load provider relationship
        result = await db.execute(
            select(LLMApiKey)
            .options(selectinload(LLMApiKey.provider))
            .where(LLMApiKey.id == api_key.id)
        )
        return result.scalar_one()
    
    @staticmethod
    async def update_key(
        db: AsyncSession,
        key_id: int,
        user_id: int,
        data: LLMApiKeyUpdate
    ) -> Optional[LLMApiKey]:
        """Update an API key."""
        api_key = await LLMKeyService.get_key(db, key_id, user_id)
        if not api_key:
            return None
        
        if data.label is not None:
            api_key.label = data.label
        
        if data.is_active is not None:
            api_key.is_active = data.is_active
            
        if data.extra_params is not None:
            api_key.extra_params = json.dumps(data.extra_params)
        
        if data.api_key:
            # Re-encrypt new key
            provider = api_key.provider
            
            # Check standard API key validation only if using standard field
            use_standard_key = True
            if provider.config_schema:
                try:
                    schema = json.loads(provider.config_schema)
                    if schema.get("use_api_key_field") is False:
                        use_standard_key = False
                except:
                    pass

            if use_standard_key:
                is_valid, error = validate_api_key(data.api_key, api_key.provider.name)
                if not is_valid:
                    raise LLMKeyServiceError(f"Invalid API key format: {error}")
                
                api_key.encrypted_key = encrypt_api_key(data.api_key)
                api_key.key_preview = mask_api_key(data.api_key)
            else:
                # Just update valid status, encryption handled in extra_params potentially
                api_key.encrypted_key = "stored_in_extra_params"
                api_key.key_preview = "config_based"
                
            api_key.is_valid = True
        
        try:
            await db.commit()
            await db.refresh(api_key)
        except IntegrityError:
            await db.rollback()
            raise LLMKeyServiceError(
                f"An API key with the label '{data.label}' already exists for this provider."
            )
        return api_key
    
    @staticmethod
    async def delete_key(
        db: AsyncSession,
        key_id: int,
        user_id: int
    ) -> bool:
        """Delete an API key."""
        api_key = await LLMKeyService.get_key(db, key_id, user_id)
        if not api_key:
            return False
        
        # Check if key is in use by any agents
        result = await db.execute(
            select(func.count(UserAIAgent.id)).where(UserAIAgent.api_key_id == key_id)
        )
        agent_count = result.scalar()
        if agent_count > 0:
            raise LLMKeyServiceError(
                f"Cannot delete key: {agent_count} agent(s) are using this key"
            )
        
        await db.delete(api_key)
        await db.commit()
        return True
    
    @staticmethod
    async def get_decrypted_key(
        db: AsyncSession,
        key_id: int,
        user_id: int
    ) -> Optional[str]:
        """Get the decrypted API key (for internal use only)."""
        api_key = await LLMKeyService.get_key(db, key_id, user_id)
        if not api_key:
            return None
        
        try:
            return decrypt_api_key(api_key.encrypted_key)
        except KeyEncryptionError:
            # Mark key as invalid
            api_key.is_valid = False
            await db.commit()
            return None
    
    @staticmethod
    async def check_user_has_key(
        db: AsyncSession,
        user_id: int,
        provider_id: int
    ) -> bool:
        """Check if user has an active key for a provider."""
        result = await db.execute(
            select(func.count(LLMApiKey.id)).where(
                LLMApiKey.user_id == user_id,
                LLMApiKey.provider_id == provider_id,
                LLMApiKey.is_active == True
            )
        )
        return result.scalar() > 0
    
    # ============================================
    # AGENTS
    # ============================================
    
    @staticmethod
    async def get_user_agents(
        db: AsyncSession,
        user_id: int,
        include_public: bool = True
    ) -> List[UserAIAgent]:
        """Get all agents for a user."""
        query = select(UserAIAgent).options(
            selectinload(UserAIAgent.provider),
            selectinload(UserAIAgent.api_key)
        )
        
        if include_public:
            query = query.where(
                (UserAIAgent.user_id == user_id) | (UserAIAgent.is_public == True)
            )
        else:
            query = query.where(UserAIAgent.user_id == user_id)
        
        query = query.order_by(UserAIAgent.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_agent(
        db: AsyncSession,
        agent_id: int,
        user_id: int
    ) -> Optional[UserAIAgent]:
        """Get a specific agent."""
        result = await db.execute(
            select(UserAIAgent)
            .options(
                selectinload(UserAIAgent.provider),
                selectinload(UserAIAgent.api_key)
            )
            .where(
                UserAIAgent.id == agent_id,
                (UserAIAgent.user_id == user_id) | (UserAIAgent.is_public == True)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_agent(
        db: AsyncSession,
        user_id: int,
        data: AIAgentCreate
    ) -> UserAIAgent:
        """Create a new AI agent."""
        # Validate provider
        provider = await LLMKeyService.get_provider(db, data.provider_id)
        if not provider:
            raise LLMKeyServiceError("Provider not found")
        
        # Validate API key belongs to user and provider
        api_key = await LLMKeyService.get_key(db, data.api_key_id, user_id)
        if not api_key:
            raise LLMKeyServiceError("API key not found")
        if api_key.provider_id != data.provider_id:
            raise LLMKeyServiceError("API key does not match selected provider")
        if not api_key.is_active:
            raise LLMKeyServiceError("API key is not active")
        
        # Create agent
        agent = UserAIAgent(
            user_id=user_id,
            provider_id=data.provider_id,
            api_key_id=data.api_key_id,
            name=data.name,
            description=data.description,
            agent_type=UserAgentType(data.type) if data.type else UserAgentType.ASSISTANT,
            model_name=data.model_name,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            system_prompt=data.system_prompt,
            is_public=data.is_public,
            status=UserAgentStatus.ACTIVE
        )
        
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        
        # Load relationships
        result = await db.execute(
            select(UserAIAgent)
            .options(
                selectinload(UserAIAgent.provider),
                selectinload(UserAIAgent.api_key)
            )
            .where(UserAIAgent.id == agent.id)
        )
        return result.scalar_one()
    
    @staticmethod
    async def update_agent(
        db: AsyncSession,
        agent_id: int,
        user_id: int,
        data: AIAgentUpdate
    ) -> Optional[UserAIAgent]:
        """Update an agent."""
        agent = await LLMKeyService.get_agent(db, agent_id, user_id)
        if not agent or agent.user_id != user_id:
            return None
        
        update_fields = data.model_dump(exclude_unset=True)
        
        for field, value in update_fields.items():
            if field == "api_key_id" and value is not None:
                # Validate new key
                new_key = await LLMKeyService.get_key(db, value, user_id)
                if not new_key or new_key.provider_id != agent.provider_id:
                    raise LLMKeyServiceError("Invalid API key")
            
            if field == "type" and value is not None:
                # Map 'type' field to 'agent_type' column
                field = "agent_type"
                value = UserAgentType(value)
            elif field == "status" and value is not None:
                value = UserAgentStatus(value)
            
            setattr(agent, field, value)
        
        await db.commit()
        await db.refresh(agent)
        return agent
    
    @staticmethod
    async def delete_agent(
        db: AsyncSession,
        agent_id: int,
        user_id: int
    ) -> bool:
        """Delete an agent."""
        agent = await LLMKeyService.get_agent(db, agent_id, user_id)
        if not agent or agent.user_id != user_id:
            return False
        
        await db.delete(agent)
        await db.commit()
        return True
    
    @staticmethod
    async def check_can_create_agent(
        db: AsyncSession,
        user_id: int,
        provider_id: int
    ) -> tuple[bool, List[LLMApiKey], str]:
        """
        Check if user can create an agent for a provider.
        
        Returns: (can_create, available_keys, message)
        """
        provider = await LLMKeyService.get_provider(db, provider_id)
        if not provider:
            return False, [], "Provider not found"
        
        if not provider.requires_api_key:
            return True, [], "No API key required for this provider"
        
        keys = await LLMKeyService.get_user_keys(
            db, user_id, provider_id=provider_id, active_only=True
        )
        
        if not keys:
            return False, [], f"Please add an API key for {provider.display_name} first"
        
        return True, keys, "Ready to create agent"


# Singleton instance
llm_key_service = LLMKeyService()
