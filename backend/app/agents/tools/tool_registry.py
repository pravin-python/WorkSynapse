"""
Tool Registry
=============

Central registry for all available agent tools.
Handles tool loading, caching, and lookup.
"""

import logging
from typing import Any, Dict, List, Optional, Type
from langchain_core.tools import BaseTool as LangChainBaseTool, StructuredTool

from app.agents.tools.base import BaseTool, ToolResult
from app.agents.orchestrator.exceptions import ToolNotFoundError
from app.agents.orchestrator.config import get_orchestrator_config
from app.services.mcp_client import MCPClient, MCPTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for agent tools.

    Manages tool registration, loading, and instantiation.
    Supports both built-in tools and MCP connectors.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._tool_instances: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}
        self._loaded = False

    def register(self, tool_class: Type[BaseTool]) -> None:
        """
        Register a tool class.

        Args:
            tool_class: Tool class to register
        """
        name = tool_class.name
        if not name:
            raise ValueError(f"Tool class {tool_class.__name__} has no name")

        self._tools[name] = tool_class

        # Track by category
        category = tool_class.category
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)

        logger.debug(f"Registered tool: {name} in category {category}")

    def register_mcp_tools(self, mcp_client: MCPClient, tools: List[MCPTool]) -> None:
        """
        Dynamically register tools from an MCP server.

        Args:
            mcp_client: The connected MCP client
            tools: List of MCP tools to register
        """
        for tool_data in tools:
            # Create a dynamic LangChain tool wrapper
            tool_name = tool_data.name
            description = tool_data.description or "No description provided"
            
            # Define the async function that calls the MCP client
            async def _mcp_tool_func(**kwargs) -> Any:
                 return await mcp_client.call_tool(tool_name, kwargs)

            # Create StructuredTool
            mcp_tool = StructuredTool.from_function(
                func=None,
                coroutine=_mcp_tool_func,
                name=tool_name,
                description=description,
                # args_schema=... # TODO: Convert JSON schema to Pydantic if needed
                # For now, relying on dynamic kwargs
            )
            
            # Store in a separate registry or special category for MCP tools
            # Here we wrap it in a BaseTool compatible class or store mostly for retrieval
            # Since our architecture expects BaseTool classes, we might need a bridge.
            # However, get_langchain_tools returns LangChainBaseTool.
            
            # We will store these in a separate dictionary for runtime lookup
            if not hasattr(self, "_dynamic_mcp_tools"):
                self._dynamic_mcp_tools = {}
            
            self._dynamic_mcp_tools[tool_name] = mcp_tool
            
            # Add to categories
            category = "mcp"
            if category not in self._categories:
                self._categories[category] = []
            if tool_name not in self._categories[category]:
                self._categories[category].append(tool_name)
                
            logger.info(f"Registered MCP tool: {tool_name}")

    def get_tool(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseTool:
        """
        Get a tool instance by name.

        Args:
            name: Tool name
            config: Optional tool configuration

        Returns:
            BaseTool instance

        Raises:
            ToolNotFoundError: If tool is not registered
        """
        if name not in self._tools:
            raise ToolNotFoundError(name)

        # Create cache key
        cache_key = f"{name}:{hash(str(config))}" if config else name

        # Return cached instance if available
        if cache_key in self._tool_instances:
            return self._tool_instances[cache_key]

        # Create new instance
        tool_class = self._tools[name]
        tool = tool_class(config=config)
        self._tool_instances[cache_key] = tool

        return tool

    def get_langchain_tool(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> LangChainBaseTool:
        """
        Get a LangChain tool by name.

        Args:
            name: Tool name
            config: Optional tool configuration

        Returns:
            LangChain BaseTool instance
        """
        tool = self.get_tool(name, config)
        return tool.to_langchain_tool()

    def get_mcp_tool(self, name: str) -> Optional[LangChainBaseTool]:
        """Get a registered MCP tool instance."""
        if hasattr(self, "_dynamic_mcp_tools") and name in self._dynamic_mcp_tools:
            return self._dynamic_mcp_tools[name]
        return None

    def get_langchain_tools(
        self,
        names: List[str],
        configs: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[LangChainBaseTool]:
        """
        Get multiple LangChain tools by name.

        Args:
            names: List of tool names
            configs: Optional dict mapping tool names to configs

        Returns:
            List of LangChain BaseTool instances
        """
        tools = []
        configs = configs or {}

        for name in names:
            try:
                tool_config = configs.get(name)
                tool = self.get_langchain_tool(name, tool_config)
                tools.append(tool)
            except ToolNotFoundError:
                logger.warning(f"Tool not found: {name}")
            except Exception as e:
                logger.error(f"Error loading tool {name}: {e}")

        # Add MCP tools if found in dynamic registry
        if hasattr(self, "_dynamic_mcp_tools"):
             for name in names:
                 if name in self._dynamic_mcp_tools:
                     tools.append(self._dynamic_mcp_tools[name])

        return tools

    def get_available_tools(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())

    def get_tools_by_category(self, category: str) -> List[str]:
        """Get tool names in a specific category."""
        return self._categories.get(category, [])

    def get_categories(self) -> List[str]:
        """Get all tool categories."""
        return list(self._categories.keys())

    def get_tools_info(self) -> List[Dict[str, Any]]:
        """Get information about all tools."""
        tools_info = []
        for name, tool_class in self._tools.items():
            try:
                # Create temporary instance to get info
                tool = tool_class()
                tools_info.append(tool.get_info())
            except Exception as e:
                logger.warning(f"Could not get info for tool {name}: {e}")
        return tools_info

    def get_tool_info(self, name: str) -> Dict[str, Any]:
        """Get information about a specific tool."""
        if name not in self._tools:
            raise ToolNotFoundError(name)

        tool_class = self._tools[name]
        tool = tool_class()
        return tool.get_info()

    def load_builtin_tools(self) -> None:
        """Load all built-in tools."""
        if self._loaded:
            return

        # Import and register built-in tools
        from app.agents.tools.builtin import (
            github_tools,
            slack_tools,
            teams_tools,
            telegram_tools,
            web_tools,
            file_tools,
        )

        # Register GitHub tools
        for tool_class in github_tools.get_tools():
            self.register(tool_class)

        # Register Slack tools
        for tool_class in slack_tools.get_tools():
            self.register(tool_class)

        # Register Teams tools
        for tool_class in teams_tools.get_tools():
            self.register(tool_class)

        # Register Telegram tools
        for tool_class in telegram_tools.get_tools():
            self.register(tool_class)

        # Register Web tools
        for tool_class in web_tools.get_tools():
            self.register(tool_class)

        # Register File tools
        for tool_class in file_tools.get_tools():
            self.register(tool_class)

        self._loaded = True
        logger.info(f"Loaded {len(self._tools)} built-in tools")

    def validate_tools_for_agent(
        self,
        tool_names: List[str],
        agent_permissions: Dict[str, bool],
    ) -> List[str]:
        """
        Validate which tools an agent can use based on permissions.

        Args:
            tool_names: List of requested tool names
            agent_permissions: Agent's permission settings

        Returns:
            List of allowed tool names
        """
        allowed = []

        for name in tool_names:
            try:
                tool = self.get_tool(name)
                if tool.validate_permissions(agent_permissions):
                    allowed.append(name)
                else:
                    logger.warning(
                        f"Tool {name} denied due to insufficient permissions"
                    )
            except ToolNotFoundError:
                logger.warning(f"Tool not found: {name}")

        return allowed


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.load_builtin_tools()
    return _registry
