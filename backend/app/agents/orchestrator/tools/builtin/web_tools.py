"""
Web Tools
=========

Tools for web operations like fetching URLs, scraping, and searching.
"""

import logging
from typing import Any, Dict, List, Optional, Type
import httpx

from app.agents.orchestrator.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class WebFetchTool(BaseTool):
    """Fetch content from a URL."""

    name = "web_fetch"
    description = "Fetch content from a URL and return the text"
    category = "web"
    required_permissions = ["can_access_internet"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch content from",
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum content length to return",
                },
            },
            "required": ["url"],
        }

    async def execute(
        self,
        url: str,
        max_length: int = 10000,
        **kwargs,
    ) -> ToolResult:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=headers,
                    timeout=30,
                    follow_redirects=True,
                )
                response.raise_for_status()

            content = response.text
            if len(content) > max_length:
                content = content[:max_length] + "... [truncated]"

            return ToolResult(
                success=True,
                data={
                    "url": str(response.url),
                    "status_code": response.status_code,
                    "content": content,
                    "content_type": response.headers.get("content-type", ""),
                },
            )

        except Exception as e:
            logger.error(f"Web fetch error: {e}")
            return ToolResult(success=False, error=str(e))


class WebSearchTool(BaseTool):
    """Search the web using DuckDuckGo."""

    name = "web_search"
    description = "Search the web using DuckDuckGo and return results"
    category = "web"
    required_permissions = ["can_access_internet"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                },
            },
            "required": ["query"],
        }

    async def execute(
        self,
        query: str,
        num_results: int = 5,
        **kwargs,
    ) -> ToolResult:
        try:
            # Use DuckDuckGo HTML search (no API key needed)
            url = "https://html.duckduckgo.com/html/"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data={"q": query},
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()

            # Parse results from HTML (simplified)
            from html.parser import HTMLParser
            
            results = []
            content = response.text

            # Simple extraction of result links and titles
            import re
            
            # Find result links
            pattern = r'class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, content)
            
            for url, title in matches[:num_results]:
                results.append({
                    "title": title.strip(),
                    "url": url,
                })

            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "count": len(results),
                },
            )

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return ToolResult(success=False, error=str(e))


class WebExtractTextTool(BaseTool):
    """Extract readable text from a webpage."""

    name = "web_extract_text"
    description = "Extract the main readable text content from a webpage"
    category = "web"
    required_permissions = ["can_access_internet"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to extract text from",
                },
            },
            "required": ["url"],
        }

    async def execute(
        self,
        url: str,
        **kwargs,
    ) -> ToolResult:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=headers,
                    timeout=30,
                    follow_redirects=True,
                )
                response.raise_for_status()

            html = response.text

            # Simple HTML to text extraction
            import re

            # Remove scripts and styles
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()

            # Limit length
            if len(text) > 15000:
                text = text[:15000] + "... [truncated]"

            return ToolResult(
                success=True,
                data={
                    "url": str(response.url),
                    "text": text,
                    "length": len(text),
                },
            )

        except Exception as e:
            logger.error(f"Web extract text error: {e}")
            return ToolResult(success=False, error=str(e))


class WebJSONApiTool(BaseTool):
    """Make a JSON API request."""

    name = "web_api_request"
    description = "Make a JSON API request (GET or POST)"
    category = "web"
    required_permissions = ["can_access_internet"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "API endpoint URL",
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method (GET or POST)",
                },
                "headers": {
                    "type": "object",
                    "description": "Request headers",
                },
                "body": {
                    "type": "object",
                    "description": "Request body for POST requests",
                },
            },
            "required": ["url"],
        }

    async def execute(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ToolResult:
        try:
            request_headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            if headers:
                request_headers.update(headers)

            async with httpx.AsyncClient() as client:
                if method.upper() == "POST":
                    response = await client.post(
                        url,
                        json=body,
                        headers=request_headers,
                        timeout=30,
                    )
                else:
                    response = await client.get(
                        url,
                        headers=request_headers,
                        timeout=30,
                    )

                response.raise_for_status()

            try:
                data = response.json()
            except Exception:
                data = response.text

            return ToolResult(
                success=True,
                data={
                    "status_code": response.status_code,
                    "response": data,
                },
            )

        except Exception as e:
            logger.error(f"Web API request error: {e}")
            return ToolResult(success=False, error=str(e))


def get_tools() -> List[Type[BaseTool]]:
    """Return all web tool classes."""
    return [
        WebFetchTool,
        WebSearchTool,
        WebExtractTextTool,
        WebJSONApiTool,
    ]
