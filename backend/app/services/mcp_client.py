"""
MCP Client Service
==================

Client for connecting to Model Context Protocol (MCP) servers.
Allows agents to discover and use tools/resources from external MCP servers.
"""

import logging
import json
import httpx
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MCPTool(BaseModel):
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any]


class MCPResource(BaseModel):
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None


class MCPClient:
    """
    Client for interacting with MCP servers.
    Supports SSE (Server-Sent Events) and STDIO (simulated via API) transport.
    """

    def __init__(self, server_url: str, auth_token: Optional[str] = None):
        """
        Initialize MCP Client.

        Args:
            server_url: Base URL of the MCP server
            auth_token: Optional authentication token
        """
        self.server_url = server_url.rstrip("/")
        self.auth_token = auth_token
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
        
        # Timeout settings
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def list_tools(self) -> List[MCPTool]:
        """
        List available tools from the MCP server.

        Returns:
            List of MCPTool objects
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.server_url}/jsonrpc",
                    headers=self.headers,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": 1,
                        "params": {}
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    logger.error(f"MCP Error list_tools: {data['error']}")
                    return []
                
                result = data.get("result", {})
                tools_data = result.get("tools", [])
                
                return [MCPTool(**tool) for tool in tools_data]
                
        except Exception as e:
            logger.error(f"Failed to list MCP tools from {self.server_url}: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a specific tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool

        Returns:
            Tool execution result
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.server_url}/jsonrpc",
                    headers=self.headers,
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "id": 2,
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    raise Exception(f"MCP Tool Error: {data['error'].get('message', 'Unknown error')}")
                
                return data.get("result", {})
                
        except Exception as e:
            logger.error(f"Failed to call MCP tool {tool_name}: {e}")
            raise

    async def list_resources(self) -> List[MCPResource]:
        """
        List available resources from the MCP server.

        Returns:
            List of MCPResource objects
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.server_url}/jsonrpc",
                    headers=self.headers,
                    json={
                        "jsonrpc": "2.0",
                        "method": "resources/list",
                        "id": 3,
                        "params": {}
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    logger.error(f"MCP Error list_resources: {data['error']}")
                    return []
                
                result = data.get("result", {})
                resources_data = result.get("resources", [])
                
                return [MCPResource(**res) for res in resources_data]
                
        except Exception as e:
            logger.error(f"Failed to list MCP resources from {self.server_url}: {e}")
            return []

    async def read_resource(self, uri: str) -> str:
        """
        Read a resource from the MCP server.

        Args:
            uri: Resource URI

        Returns:
            Content of the resource
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.server_url}/jsonrpc",
                    headers=self.headers,
                    json={
                        "jsonrpc": "2.0",
                        "method": "resources/read",
                        "id": 4,
                        "params": {
                            "uri": uri
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    raise Exception(f"MCP Resource Error: {data['error'].get('message', 'Unknown error')}")
                
                result = data.get("result", {})
                contents = result.get("contents", [])
                
                if not contents:
                    return ""
                
                # Check for text or blob
                content_item = contents[0]
                if "text" in content_item:
                    return content_item["text"]
                elif "blob" in content_item:
                    return f"[Binary Data: {content_item.get('mimeType', 'unknown')}]"
                
                return str(contents)
                
        except Exception as e:
            logger.error(f"Failed to read MCP resource {uri}: {e}")
            raise
