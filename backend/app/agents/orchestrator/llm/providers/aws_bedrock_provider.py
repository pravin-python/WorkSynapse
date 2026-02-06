"""
AWS Bedrock LLM Provider
========================

AWS Bedrock integration using LangChain.
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_aws import ChatBedrock

from app.agents.orchestrator.llm.providers.base import BaseLLMProvider, LLMResponse
from app.agents.orchestrator.config import LLMProviderConfig
from app.agents.orchestrator.exceptions import LLMProviderError

logger = logging.getLogger(__name__)


class BedrockProvider(BaseLLMProvider):
    """
    AWS Bedrock LLM provider using LangChain's ChatBedrock.
    """

    def _create_client(self) -> BaseChatModel:
        """Create the ChatBedrock client."""
        # For Bedrock, we need AWS credentials
        aws_access_key = getattr(self.config, "aws_access_key_id", None)
        aws_secret_key = getattr(self.config, "aws_secret_access_key", None)
        region_name = getattr(self.config, "region_name", "us-east-1")
        
        # Validating credentials - either via config or environment (handled by boto3 if None)
        # If passed explicitly in config, use them.
        
        client_kwargs = {}
        if aws_access_key and aws_secret_key:
            client_kwargs["aws_access_key_id"] = aws_access_key
            client_kwargs["aws_secret_access_key"] = aws_secret_key
        
        if region_name:
            client_kwargs["region_name"] = region_name

        return ChatBedrock(
            model_id=self.config.default_model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            **client_kwargs
        )

    def _create_client_with_model(self, model_name: str) -> BaseChatModel:
        """Create a client with a specific model."""
        aws_access_key = getattr(self.config, "aws_access_key_id", None)
        aws_secret_key = getattr(self.config, "aws_secret_access_key", None)
        region_name = getattr(self.config, "region_name", "us-east-1")
        
        client_kwargs = {}
        if aws_access_key and aws_secret_key:
            client_kwargs["aws_access_key_id"] = aws_access_key
            client_kwargs["aws_secret_access_key"] = aws_secret_key
        
        if region_name:
            client_kwargs["region_name"] = region_name

        return ChatBedrock(
            model_id=model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            **client_kwargs
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
        """Generate a response using AWS Bedrock."""
        try:
            client = self.get_langchain_model(model) if model else self.client

            # Apply optional parameters
            if temperature is not None:
                client.temperature = temperature
            if max_tokens is not None:
                client.max_tokens = max_tokens

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
            logger.error(f"AWS Bedrock generation error: {e}")
            raise LLMProviderError("aws_bedrock", str(e))

    async def stream(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a response from AWS Bedrock."""
        try:
            client = self.get_langchain_model(model) if model else self.client

            # Apply optional parameters
            if temperature is not None:
                client.temperature = temperature
            if max_tokens is not None:
                client.max_tokens = max_tokens

            # Bind tools if provided
            if tools:
                client = client.bind_tools(tools)

            # Stream response
            async for chunk in client.astream(messages, **kwargs):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

        except Exception as e:
            logger.error(f"AWS Bedrock streaming error: {e}")
            raise LLMProviderError("aws_bedrock", str(e))
