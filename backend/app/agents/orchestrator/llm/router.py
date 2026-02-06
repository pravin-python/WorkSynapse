"""
LLM Router
==========

Dynamic LLM provider routing based on agent configuration.
Routes requests to the appropriate provider (OpenAI, Ollama, Gemini, Claude, HuggingFace).
"""

import logging
from typing import Any, Dict, List, Optional, Type
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool

from app.agents.orchestrator.config import OrchestratorConfig, LLMProviderConfig, get_orchestrator_config
from app.agents.orchestrator.exceptions import LLMProviderError, LLMProviderNotFoundError
from app.agents.orchestrator.llm.providers.base import BaseLLMProvider, LLMResponse
from app.agents.orchestrator.llm.providers.openai_provider import OpenAIProvider
from app.agents.orchestrator.llm.providers.ollama_provider import OllamaProvider
from app.agents.orchestrator.llm.providers.gemini_provider import GeminiProvider
from app.agents.orchestrator.llm.providers.claude_provider import ClaudeProvider
from app.agents.orchestrator.llm.providers.huggingface_provider import HuggingFaceProvider
from app.agents.orchestrator.llm.providers.groq_provider import GroqProvider
from app.agents.orchestrator.llm.providers.azure_openai_provider import AzureOpenAIProvider
from app.agents.orchestrator.llm.providers.aws_bedrock_provider import BedrockProvider
from app.agents.orchestrator.llm.providers.deepseek_provider import DeepSeekProvider

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    LLM Router for dynamic provider selection.

    Routes requests to the appropriate LLM provider based on
    agent configuration. Supports multiple providers and
    automatic fallback.
    """

    # Provider class mapping
    PROVIDER_CLASSES: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
        "huggingface": HuggingFaceProvider,
        "groq": GroqProvider,
        "azure_openai": AzureOpenAIProvider,
        "aws_bedrock": BedrockProvider,
        "deepseek": DeepSeekProvider,
    }

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize the LLM Router.

        Args:
            config: Orchestrator configuration. Uses default if not provided.
        """
        self.config = config or get_orchestrator_config()
        self._providers: Dict[str, BaseLLMProvider] = {}

    def get_provider(self, provider_name: str) -> BaseLLMProvider:
        """
        Get or create an LLM provider instance.

        Args:
            provider_name: Name of the provider (openai, ollama, etc.)

        Returns:
            BaseLLMProvider instance

        Raises:
            LLMProviderNotFoundError: If provider is not supported
        """
        provider_name = provider_name.lower()

        # Return cached provider if available
        if provider_name in self._providers:
            return self._providers[provider_name]

        # Validate provider name
        if provider_name not in self.PROVIDER_CLASSES:
            raise LLMProviderNotFoundError(provider_name)

        # Get provider configuration
        provider_config = self.config.get_provider_config(provider_name)
        if not provider_config:
            raise LLMProviderError(provider_name, "Provider configuration not found")

        # Create provider instance
        provider_class = self.PROVIDER_CLASSES[provider_name]
        provider = provider_class(provider_config)

        # Cache and return
        self._providers[provider_name] = provider
        return provider

    def get_langchain_model(
        self,
        provider_name: str,
        model_name: Optional[str] = None,
    ) -> BaseChatModel:
        """
        Get a LangChain model for the specified provider.

        Args:
            provider_name: Name of the provider
            model_name: Optional specific model name

        Returns:
            LangChain BaseChatModel instance
        """
        provider = self.get_provider(provider_name)
        return provider.get_langchain_model(model_name)

    async def generate(
        self,
        provider_name: str,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a response using the specified provider.

        Args:
            provider_name: Name of the provider to use
            messages: List of chat messages
            tools: Optional list of tools
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            **kwargs: Additional arguments

        Returns:
            LLMResponse with the model's response
        """
        provider = self.get_provider(provider_name)

        return await provider.generate(
            messages=messages,
            tools=tools,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def stream(
        self,
        provider_name: str,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        """
        Stream a response using the specified provider.

        Args:
            provider_name: Name of the provider to use
            messages: List of chat messages
            tools: Optional list of tools
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            **kwargs: Additional arguments

        Yields:
            String chunks of the response
        """
        provider = self.get_provider(provider_name)

        async for chunk in provider.stream(
            messages=messages,
            tools=tools,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield chunk

    def get_available_providers(self) -> List[str]:
        """Get list of providers with valid credentials."""
        return self.config.get_available_providers()

    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """
        Get information about a specific provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Dictionary with provider information
        """
        provider_config = self.config.get_provider_config(provider_name)
        if not provider_config:
            raise LLMProviderNotFoundError(provider_name)

        # Check if provider has valid credentials
        available_providers = self.config.get_available_providers()
        is_available = provider_name in available_providers

        return {
            "name": provider_name,
            "display_name": provider_name.title(),
            "available": is_available,
            "models": provider_config.available_models,
            "default_model": provider_config.default_model,
            "supports_streaming": True,
            "supports_tools": provider_name != "huggingface",
        }

    def get_all_providers_info(self) -> List[Dict[str, Any]]:
        """Get information about all supported providers."""
        providers_info = []
        for provider_name in self.PROVIDER_CLASSES.keys():
            try:
                info = self.get_provider_info(provider_name)
                providers_info.append(info)
            except Exception as e:
                logger.warning(f"Could not get info for provider {provider_name}: {e}")
        return providers_info

    def validate_provider_and_model(
        self,
        provider_name: str,
        model_name: Optional[str] = None,
    ) -> bool:
        """
        Validate that a provider and model combination is valid.

        Args:
            provider_name: Name of the provider
            model_name: Optional model name to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            provider = self.get_provider(provider_name)
            if model_name:
                return provider.validate_model(model_name)
            return True
        except Exception:
            return False


# Global router instance
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get the global LLM router instance."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
