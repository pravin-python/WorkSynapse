"""
Provider Router
===============

Dynamic LLM provider routing.
"""

from typing import Any, Dict, List, Optional, Type
from langchain_core.language_models import BaseChatModel

from app.agents.orchestrator.config import OrchestratorConfig, get_orchestrator_config
from app.agents.providers.base import BaseLLMProvider
from app.agents.providers.openai_provider import OpenAIProvider
from app.agents.providers.ollama_provider import OllamaProvider
from app.agents.providers.gemini_provider import GeminiProvider
from app.agents.providers.claude_provider import ClaudeProvider
from app.agents.providers.huggingface_provider import HuggingFaceProvider
from app.agents.providers.groq_provider import GroqProvider
from app.agents.providers.azure_openai_provider import AzureOpenAIProvider
from app.agents.providers.aws_bedrock_provider import BedrockProvider
from app.agents.providers.deepseek_provider import DeepSeekProvider
from app.agents.orchestrator.exceptions import LLMProviderNotFoundError

class ProviderRouter:
    """
    Dynamic LLM Provider Router.
    """

    PROVIDER_CLASSES: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
        "gemini": GeminiProvider,
        "google": GeminiProvider,
        "claude": ClaudeProvider,
        "huggingface": HuggingFaceProvider,
        "groq": GroqProvider,
        "azure_openai": AzureOpenAIProvider,
        "aws_bedrock": BedrockProvider,
        "deepseek": DeepSeekProvider,
    }

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or get_orchestrator_config()

    def get_provider(self, provider_name: str) -> BaseLLMProvider:
        provider_name = provider_name.lower()
        if provider_name not in self.PROVIDER_CLASSES:
             raise LLMProviderNotFoundError(provider_name)

        provider_config = self.config.get_provider_config(provider_name)
        provider_class = self.PROVIDER_CLASSES[provider_name]
        return provider_class(provider_config)

    @classmethod
    def load(cls, provider_name: str, user_id: Optional[str] = None) -> BaseChatModel:
        """
        Load a provider dynamically.
        """
        router = cls()
        # In a real app, user_id might be used to fetch user-specific keys
        # For now, we use the global config
        provider = router.get_provider(provider_name)
        return provider.get_langchain_model()

    def get_langchain_model(self, provider_name: str, model_name: Optional[str] = None) -> BaseChatModel:
        provider = self.get_provider(provider_name)
        return provider.get_langchain_model(model_name)
