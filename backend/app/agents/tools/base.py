"""
Base Tool Definition
====================

Base class and utilities for agent tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Callable
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool as LangChainBaseTool, StructuredTool
from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun


class ToolResult(BaseModel):
    """Standardized tool execution result."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """
    Base class for WorkSynapse agent tools.

    All tools must implement this interface to ensure
    consistent behavior and easy integration with LangChain.
    """

    # Tool metadata
    name: str = ""
    description: str = ""
    category: str = "general"

    # Configuration
    requires_config: bool = False
    required_permissions: List[str] = []

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the tool.

        Args:
            config: Optional tool-specific configuration
        """
        self.config = config or {}

    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema for tool parameters.

        Returns:
            Dictionary describing the parameters
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with the given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with execution outcome
        """
        pass

    def to_langchain_tool(self) -> LangChainBaseTool:
        """
        Convert this tool to a LangChain tool.

        Returns:
            LangChain StructuredTool instance
        """
        # Create async function wrapper
        async def tool_func(**kwargs) -> str:
            result = await self.execute(**kwargs)
            if result.success:
                return str(result.data)
            else:
                return f"Error: {result.error}"

        # Create the StructuredTool
        return StructuredTool.from_function(
            func=None,
            coroutine=tool_func,
            name=self.name,
            description=self.description,
            args_schema=self._create_args_schema(),
            return_direct=False,
        )

    def _create_args_schema(self) -> Optional[Type[BaseModel]]:
        """Create a Pydantic model from the parameters schema."""
        schema = self.get_parameters_schema()
        if not schema or not schema.get("properties"):
            return None

        # Dynamically create a Pydantic model
        from pydantic import create_model

        fields = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for name, prop in properties.items():
            field_type = self._get_python_type(prop.get("type", "string"))
            default = ... if name in required else None
            description = prop.get("description", "")
            fields[name] = (field_type, Field(default=default, description=description))

        return create_model(f"{self.name}Args", **fields)

    @staticmethod
    def _get_python_type(json_type: str):
        """Convert JSON schema type to Python type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        return type_map.get(json_type, str)

    def validate_permissions(self, agent_permissions: Dict[str, bool]) -> bool:
        """
        Check if the agent has required permissions for this tool.

        Args:
            agent_permissions: Dictionary of agent permissions

        Returns:
            True if all required permissions are granted
        """
        for permission in self.required_permissions:
            if not agent_permissions.get(permission, False):
                return False
        return True

    def get_info(self) -> Dict[str, Any]:
        """Get tool information for API responses."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.get_parameters_schema(),
            "requires_config": self.requires_config,
            "required_permissions": self.required_permissions,
        }
