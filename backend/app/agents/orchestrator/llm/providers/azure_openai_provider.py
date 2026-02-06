"""
Azure OpenAI LLM Provider
=========================

Azure OpenAI integration using LangChain.
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_openai import AzureChatOpenAI

from app.agents.orchestrator.llm.providers.base import BaseLLMProvider, LLMResponse
from app.agents.orchestrator.config import LLMProviderConfig
from app.agents.orchestrator.exceptions import LLMProviderError

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(BaseLLMProvider):
    """
    Azure OpenAI LLM provider using LangChain's AzureChatOpenAI.
    """

    def _create_client(self) -> BaseChatModel:
        """Create the AzureChatOpenAI client."""
        if not self.config.api_key:
            raise LLMProviderError("azure_openai", "API key not configured")
        
        # Azure specific config
        # We expect these to be available in the config object
        # For system config, they come from env vars.
        # For user config, they should be passed in the config object.
        azure_endpoint = getattr(self.config, "azure_endpoint", None)
        deployment_name = getattr(self.config, "deployment_name", None)
        api_version = getattr(self.config, "api_version", "2023-05-15")
        
        if not azure_endpoint:
            raise LLMProviderError("azure_openai", "Azure endpoint not configured")
        if not deployment_name:
            raise LLMProviderError("azure_openai", "Deployment name not configured")

        return AzureChatOpenAI(
            api_key=self.config.api_key,
            azure_endpoint=azure_endpoint,
            deployment_name=deployment_name,
            api_version=api_version,
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
        """Generate a response using Azure OpenAI."""
        try:
            client = self.client

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
                finish_reason=getattr(response, "response_metadata", {}).get("finish_reason"),
            )

        except Exception as e:
            logger.error(f"Azure OpenAI generation error: {e}")
            raise LLMProviderError("azure_openai", str(e))

    async def stream(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a response from Azure OpenAI."""
        try:
            client = self.client

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
            logger.error(f"Azure OpenAI streaming error: {e}")
            raise LLMProviderError("azure_openai", str(e))
