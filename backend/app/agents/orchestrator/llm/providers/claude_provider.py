"""
Anthropic Claude LLM Provider
=============================

Anthropic Claude models integration using LangChain.
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_anthropic import ChatAnthropic

from app.agents.orchestrator.llm.providers.base import BaseLLMProvider, LLMResponse
from app.agents.orchestrator.config import LLMProviderConfig
from app.agents.orchestrator.exceptions import LLMProviderError

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseLLMProvider):
    """
    Anthropic Claude LLM provider using LangChain.

    Supports Claude 3 (Opus, Sonnet, Haiku) with
    streaming and tool calling capabilities.
    """

    def _create_client(self) -> BaseChatModel:
        """Create the ChatAnthropic client."""
        if not self.config.api_key:
            raise LLMProviderError("claude", "Anthropic API key not configured")

        return ChatAnthropic(
            api_key=self.config.api_key,
            model=self.config.default_model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

    def _create_client_with_model(self, model_name: str) -> BaseChatModel:
        """Create a ChatAnthropic client with a specific model."""
        if not self.config.api_key:
            raise LLMProviderError("claude", "Anthropic API key not configured")

        return ChatAnthropic(
            api_key=self.config.api_key,
            model=model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
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
        """Generate a response using Claude."""
        try:
            client = self.get_langchain_model(model) if model else self.client

            # Apply optional parameters
            if temperature is not None:
                client = client.bind(temperature=temperature)
            if max_tokens is not None:
                client = client.bind(max_tokens=max_tokens)

            # Bind tools if provided
            if tools:
                client = client.bind_tools(tools)

            # Generate response
            response: AIMessage = await client.ainvoke(messages, **kwargs)

            # Extract usage info
            usage = getattr(response, "usage_metadata", None) or {}

            # Extract tool calls
            tool_calls = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tc in response.tool_calls:
                    tool_calls.append({
                        "id": tc.get("id", ""),
                        "name": tc.get("name", ""),
                        "args": tc.get("args", {}),
                    })

            return LLMResponse(
                content=response.content if isinstance(response.content, str) else "",
                tool_calls=tool_calls,
                tokens_input=usage.get("input_tokens", 0) if isinstance(usage, dict) else 0,
                tokens_output=usage.get("output_tokens", 0) if isinstance(usage, dict) else 0,
                tokens_total=usage.get("total_tokens", 0) if isinstance(usage, dict) else 0,
                model=model or self.config.default_model,
                finish_reason=getattr(response, "response_metadata", {}).get("stop_reason"),
            )

        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise LLMProviderError("claude", str(e))

    async def stream(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a response from Claude."""
        try:
            client = self.get_langchain_model(model) if model else self.client

            # Apply optional parameters
            if temperature is not None:
                client = client.bind(temperature=temperature)
            if max_tokens is not None:
                client = client.bind(max_tokens=max_tokens)

            # Bind tools if provided
            if tools:
                client = client.bind_tools(tools)

            # Stream response
            async for chunk in client.astream(messages, **kwargs):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

        except Exception as e:
            logger.error(f"Claude streaming error: {e}")
            raise LLMProviderError("claude", str(e))

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_tools(self) -> bool:
        return True
