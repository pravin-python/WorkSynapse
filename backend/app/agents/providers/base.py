"""
Base LLM Provider
=================

Abstract base class for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.agents.orchestrator.config import LLMProviderConfig


class LLMResponse(BaseModel):
    """Standardized LLM response."""

    content: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    model: str = ""
    finish_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM providers must implement this interface to ensure
    consistent behavior across different providers.
    """

    def __init__(self, config: LLMProviderConfig):
        self.config = config
        self.name = config.name
        self._client: Optional[BaseChatModel] = None

    @property
    def client(self) -> BaseChatModel:
        """Get the LangChain chat model client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    @abstractmethod
    def _create_client(self) -> BaseChatModel:
        """Create and return the LangChain chat model client."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            messages: List of chat messages
            tools: Optional list of tools the model can use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments

        Returns:
            LLMResponse with the model's response
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream a response from the LLM.

        Args:
            messages: List of chat messages
            tools: Optional list of tools the model can use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments

        Yields:
            String chunks of the response
        """
        pass

    def get_langchain_model(self, model_name: Optional[str] = None) -> BaseChatModel:
        """Get the underlying LangChain model, optionally with a different model name."""
        if model_name and model_name != self.config.default_model:
            # Create a new client with the specified model
            return self._create_client_with_model(model_name)
        return self.client

    def _create_client_with_model(self, model_name: str) -> BaseChatModel:
        """Create a client with a specific model. Override in subclasses."""
        return self._create_client()

    def validate_model(self, model_name: str) -> bool:
        """Check if a model is available for this provider."""
        return model_name in self.config.available_models

    @property
    def available_models(self) -> List[str]:
        """Get list of available models."""
        return self.config.available_models

    @property
    def default_model(self) -> str:
        """Get the default model."""
        return self.config.default_model

    @property
    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming."""
        return True

    @property
    def supports_tools(self) -> bool:
        """Whether this provider supports tool calling."""
        return True

    def convert_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """Convert dict messages to LangChain message objects."""
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "user" or role == "human":
                converted.append(HumanMessage(content=content))
            elif role == "assistant" or role == "ai":
                converted.append(AIMessage(content=content))
            else:
                converted.append(HumanMessage(content=content))

        return converted
