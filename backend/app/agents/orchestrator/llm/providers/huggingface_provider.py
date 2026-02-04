"""
HuggingFace LLM Provider
========================

HuggingFace models integration using LangChain.
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from app.agents.orchestrator.llm.providers.base import BaseLLMProvider, LLMResponse
from app.agents.orchestrator.config import LLMProviderConfig
from app.agents.orchestrator.exceptions import LLMProviderError

logger = logging.getLogger(__name__)


class HuggingFaceProvider(BaseLLMProvider):
    """
    HuggingFace LLM provider using LangChain.

    Supports HuggingFace Hub models and inference endpoints.
    """

    def _create_client(self) -> BaseChatModel:
        """Create the HuggingFace client."""
        if not self.config.api_key:
            raise LLMProviderError("huggingface", "HuggingFace API key not configured")

        # If a custom endpoint URL is provided, use HuggingFaceEndpoint
        if self.config.base_url:
            llm = HuggingFaceEndpoint(
                endpoint_url=self.config.base_url,
                huggingfacehub_api_token=self.config.api_key,
                task="text-generation",
                max_new_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
            return ChatHuggingFace(llm=llm)
        else:
            # Use HuggingFace Hub inference API
            llm = HuggingFaceEndpoint(
                repo_id=self.config.default_model,
                huggingfacehub_api_token=self.config.api_key,
                task="text-generation",
                max_new_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
            return ChatHuggingFace(llm=llm)

    def _create_client_with_model(self, model_name: str) -> BaseChatModel:
        """Create a HuggingFace client with a specific model."""
        if not self.config.api_key:
            raise LLMProviderError("huggingface", "HuggingFace API key not configured")

        llm = HuggingFaceEndpoint(
            repo_id=model_name,
            huggingfacehub_api_token=self.config.api_key,
            task="text-generation",
            max_new_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        return ChatHuggingFace(llm=llm)

    async def generate(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate a response using HuggingFace."""
        try:
            client = self.get_langchain_model(model) if model else self.client

            # Bind tools if provided (not all HF models support this)
            if tools:
                try:
                    client = client.bind_tools(tools)
                except Exception as e:
                    logger.warning(f"HuggingFace model doesn't support tool binding: {e}")

            # Generate response
            response: AIMessage = await client.ainvoke(messages, **kwargs)

            # Extract content
            content = response.content if isinstance(response.content, str) else ""

            # Extract tool calls if any
            tool_calls = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tc in response.tool_calls:
                    tool_calls.append({
                        "id": tc.get("id", ""),
                        "name": tc.get("name", ""),
                        "args": tc.get("args", {}),
                    })

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                tokens_input=0,  # HF may not provide token counts
                tokens_output=len(content.split()) * 2,  # Rough estimate
                tokens_total=len(content.split()) * 2,
                model=model or self.config.default_model,
                finish_reason="stop",
            )

        except Exception as e:
            logger.error(f"HuggingFace generation error: {e}")
            raise LLMProviderError("huggingface", str(e))

    async def stream(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a response from HuggingFace."""
        try:
            client = self.get_langchain_model(model) if model else self.client

            # Stream response
            async for chunk in client.astream(messages, **kwargs):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

        except Exception as e:
            logger.error(f"HuggingFace streaming error: {e}")
            raise LLMProviderError("huggingface", str(e))

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def supports_tools(self) -> bool:
        # Limited tool support depending on the model
        return False
