"""
Orchestrator Configuration
==========================

Configuration settings for the Agent Orchestrator.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class LLMProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: str
    available_models: List[str] = Field(default_factory=list)
    timeout: int = 60
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Azure OpenAI specific
    azure_endpoint: Optional[str] = None
    deployment_name: Optional[str] = None
    api_version: Optional[str] = None
    
    # AWS Bedrock specific
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    region_name: Optional[str] = None


class MemoryConfig(BaseModel):
    """Configuration for memory systems."""

    # Conversation memory
    conversation_max_messages: int = 50
    conversation_ttl_hours: int = 24

    # Vector memory
    vector_store_type: str = "chroma"  # chroma, redis, postgresql
    vector_collection_prefix: str = "worksynapse_agent_"
    embedding_model: str = "text-embedding-3-small"
    vector_k_results: int = 5

    # Session memory
    session_ttl_hours: int = 2


class SecurityConfig(BaseModel):
    """Security configuration."""

    # Prompt injection protection
    enable_prompt_guard: bool = True
    blocked_patterns: List[str] = Field(
        default_factory=lambda: [
            r"ignore (previous|above|all) instructions",
            r"disregard (previous|above|all)",
            r"you are now",
            r"pretend (you are|to be)",
            r"act as if",
            r"forget (everything|your instructions)",
            r"new instruction:",
            r"system prompt:",
            r"developer mode",
            r"jailbreak",
        ]
    )

    # Rate limiting
    rate_limit_requests_per_minute: int = 30
    rate_limit_tokens_per_minute: int = 100000

    # Permissions
    default_permissions: Dict[str, bool] = Field(
        default_factory=lambda: {
            "can_access_internet": True,
            "can_access_files": False,
            "can_execute_code": False,
            "can_send_emails": False,
            "can_modify_data": False,
        }
    )


class OrchestratorConfig(BaseSettings):
    """Main orchestrator configuration."""

    model_config = SettingsConfigDict(
        env_prefix="ORCHESTRATOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ========================
    # GENERAL SETTINGS
    # ========================
    debug: bool = False
    log_level: str = "INFO"
    max_concurrent_agents: int = 100
    execution_timeout_seconds: int = 300

    # ========================
    # LLM PROVIDERS
    # ========================
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_default_model: str = "gpt-4o"
    openai_base_url: Optional[str] = None

    # Ollama (local)
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.1"

    # Google Gemini
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_default_model: str = "gemini-1.5-pro"

    # Anthropic Claude
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    claude_default_model: str = "claude-3-5-sonnet-latest"

    # HuggingFace
    huggingface_api_key: Optional[str] = Field(default=None, alias="HUGGINGFACE_API_KEY")
    huggingface_default_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    huggingface_endpoint_url: Optional[str] = None

    # Groq
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    groq_default_model: str = "llama3-70b-8192"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # Azure OpenAI
    azure_openai_api_key: Optional[str] = Field(default=None, alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: Optional[str] = Field(default=None, alias="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: str = Field(default="2023-05-15", alias="AZURE_OPENAI_API_VERSION")
    azure_openai_default_model: str = "gpt-4"

    # AWS Bedrock
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region_name: str = Field(default="us-east-1", alias="AWS_DEFAULT_REGION")
    bedrock_default_model: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    # DeepSeek
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_default_model: str = "deepseek-chat"

    # ========================
    # MEMORY
    # ========================
    memory: MemoryConfig = Field(default_factory=MemoryConfig)

    # Vector DB
    chroma_persist_directory: str = "./data/chroma"
    redis_vector_url: Optional[str] = None

    # ========================
    # SECURITY
    # ========================
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # ========================
    # MCP TOOLS
    # ========================
    # GitHub
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    github_api_url: str = "https://api.github.com"

    # Slack
    slack_bot_token: Optional[str] = Field(default=None, alias="SLACK_BOT_TOKEN")
    slack_app_token: Optional[str] = Field(default=None, alias="SLACK_APP_TOKEN")

    # Microsoft Teams
    teams_webhook_url: Optional[str] = Field(default=None, alias="TEAMS_WEBHOOK_URL")

    # Telegram
    telegram_bot_token: Optional[str] = Field(default=None, alias="TELEGRAM_BOT_TOKEN")

    def get_provider_config(self, provider: str) -> LLMProviderConfig:
        """Get configuration for a specific LLM provider."""
        providers = {
            "openai": LLMProviderConfig(
                name="openai",
                api_key=self.openai_api_key,
                base_url=self.openai_base_url,
                default_model=self.openai_default_model,
                available_models=[
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-4-turbo",
                    "gpt-4",
                    "gpt-3.5-turbo",
                ],
            ),
            "ollama": LLMProviderConfig(
                name="ollama",
                base_url=self.ollama_base_url,
                default_model=self.ollama_default_model,
                available_models=["llama3.1", "llama3", "mistral", "codellama", "phi3"],
            ),
            "gemini": LLMProviderConfig(
                name="gemini",
                api_key=self.google_api_key,
                default_model=self.gemini_default_model,
                available_models=[
                    "gemini-1.5-pro",
                    "gemini-1.5-flash",
                    "gemini-1.0-pro",
                ],
            ),
            "claude": LLMProviderConfig(
                name="claude",
                api_key=self.anthropic_api_key,
                default_model=self.claude_default_model,
                available_models=[
                    "claude-3-5-sonnet-latest",
                    "claude-3-opus-latest",
                    "claude-3-haiku-20240307",
                ],
            ),
            "huggingface": LLMProviderConfig(
                name="huggingface",
                api_key=self.huggingface_api_key,
                base_url=self.huggingface_endpoint_url,
                default_model=self.huggingface_default_model,
                available_models=[
                    "meta-llama/Llama-3.1-8B-Instruct",
                    "mistralai/Mistral-7B-Instruct-v0.3",
                    "microsoft/Phi-3-mini-4k-instruct",
                ],
            ),
            "groq": LLMProviderConfig(
                name="groq",
                api_key=self.groq_api_key,
                base_url=self.groq_base_url,
                default_model=self.groq_default_model,
                available_models=[
                    "llama3-70b-8192",
                    "mixtral-8x7b-32768",
                    "gemma2-9b-it",
                    "gemma-7b-it",
                ],
            ),
            "azure_openai": LLMProviderConfig(
                name="azure_openai",
                api_key=self.azure_openai_api_key,
                default_model=self.azure_openai_default_model,
                azure_endpoint=self.azure_openai_endpoint,
                deployment_name=self.azure_openai_deployment,
                api_version=self.azure_openai_api_version,
                available_models=["gpt-4", "gpt-35-turbo"],
            ),
            "aws_bedrock": LLMProviderConfig(
                name="aws_bedrock",
                default_model=self.bedrock_default_model,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region_name,
                available_models=[
                    "anthropic.claude-3-sonnet-20240229-v1:0",
                    "anthropic.claude-3-haiku-20240307-v1:0",
                    "amazon.titan-text-express-v1"
                ],
            ),
            "deepseek": LLMProviderConfig(
                name="deepseek",
                api_key=self.deepseek_api_key,
                base_url=self.deepseek_base_url,
                default_model=self.deepseek_default_model,
                available_models=["deepseek-chat", "deepseek-coder"],
            ),
        }
        return providers.get(provider)

    def get_available_providers(self) -> List[str]:
        """Get list of providers with valid credentials."""
        available = ["ollama"]  # Always available (local)

        if self.openai_api_key:
            available.append("openai")
        if self.google_api_key:
            available.append("gemini")
        if self.anthropic_api_key:
            available.append("claude")
        if self.huggingface_api_key:
            available.append("huggingface")
        if self.groq_api_key:
            available.append("groq")
        if self.azure_openai_api_key:
            available.append("azure_openai")
        if self.aws_access_key_id and self.aws_secret_access_key:
            available.append("aws_bedrock")
        if self.deepseek_api_key:
            available.append("deepseek")

        return available


@lru_cache()
def get_orchestrator_config() -> OrchestratorConfig:
    """Get cached orchestrator configuration."""
    return OrchestratorConfig()


# Global config instance
orchestrator_config = get_orchestrator_config()
