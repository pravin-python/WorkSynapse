"""
Ollama LLM Provider
===================

Local Ollama models integration using LangChain.
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama

from app.agents.providers.base import BaseLLMProvider, LLMResponse
from app.agents.orchestrator.config import LLMProviderConfig
from app.agents.orchestrator.exceptions import LLMProviderError

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama LLM provider for local model inference.

    Supports local models like Llama, Mistral, CodeLlama, etc.
    No API key required - runs on local hardware.
    """

    def _create_client(self) -> BaseChatModel:
        """Create the ChatOllama client."""
        return ChatOllama(
            model=self.config.default_model,
            base_url=self.config.base_url or "http://localhost:11434",
            temperature=self.config.temperature,
            num_predict=self.config.max_tokens,
        )

    def _create_client_with_model(self, model_name: str) -> BaseChatModel:
        """Create a ChatOllama client with a specific model."""
        return ChatOllama(
            model=model_name,
            base_url=self.config.base_url or "http://localhost:11434",
            temperature=self.config.temperature,
            num_predict=self.config.max_tokens,
        )

    async def generate(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a response using Ollama."""
        try:
            client = self.get_langchain_model(model) if model else self.client

            # Apply optional parameters
            if temperature is not None:
                client = client.bind(temperature=temperature)
            if max_tokens is not None:
                client = client.bind(num_predict=max_tokens)

            # Bind tools if provided and model supports it
            if tools:
                client = client.bind_tools(tools)

            # Generate response
            response: AIMessage = await client.ainvoke(messages, **kwargs)

            # Extract tool calls
            tool_calls = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tc in response.tool_calls:
                    tool_calls.append({
                        "id": tc.get("id", ""),
                        "name": tc.get("name", ""),
                        "args": tc.get("args", {}),
                    })

            # Ollama doesn't provide token counts in the same way
            content = response.content if isinstance(response.content, str) else ""

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                tokens_input=0,  # Ollama doesn't provide input tokens
                tokens_output=len(content.split()) * 2,  # Rough estimate
                tokens_total=len(content.split()) * 2,
                model=model or self.config.default_model,
                finish_reason="stop",
            )

        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise LLMProviderError("ollama", str(e))

    async def stream(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a response from Ollama."""
        try:
            client = self.get_langchain_model(model) if model else self.client

            # Apply optional parameters
            if temperature is not None:
                client = client.bind(temperature=temperature)
            if max_tokens is not None:
                client = client.bind(num_predict=max_tokens)

            # Bind tools if provided
            if tools:
                client = client.bind_tools(tools)

            # Stream response
            async for chunk in client.astream(messages, **kwargs):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise LLMProviderError("ollama", str(e))

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_tools(self) -> bool:
        # Tool support depends on the model
        return True
