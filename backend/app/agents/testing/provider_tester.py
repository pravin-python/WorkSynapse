"""
Provider Tester
===============

Test LLM providers.
"""

from typing import Tuple
from app.agents.providers.provider_router import ProviderRouter

class ProviderTester:
    """
    Test LLM providers.
    """

    async def test_provider(self, provider_name: str, model_name: str) -> Tuple[bool, str]:
        """
        Test if a provider is working.
        """
        try:
            llm = ProviderRouter().get_langchain_model(provider_name, model_name)
            # Simple ping
            response = await llm.ainvoke("Hello, this is a connectivity test. Respond with 'OK'.")
            content = response.content if hasattr(response, 'content') else str(response)
            return True, str(content)
        except Exception as e:
            return False, str(e)
