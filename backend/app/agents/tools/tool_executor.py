"""
Tool Executor
=============

Executes tools safely with validation, permissions, and error handling.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from langchain_core.tools import BaseTool as LangChainBaseTool

from app.agents.tools.base import BaseTool, ToolResult
from app.agents.orchestrator.exceptions import ToolExecutionError, PermissionDeniedError
from app.agents.tools.tool_registry import ToolRegistry, get_tool_registry

logger = logging.getLogger(__name__)

class ToolExecutor:
    """
    Executes tools safely with validation and error handling.
    """

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or get_tool_registry()

    async def execute(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        agent_permissions: Optional[Dict[str, bool]] = None,
        timeout: int = 30
    ) -> ToolResult:
        """
        Execute a tool safely.
        """
        try:
            # 1. Get Tool
            tool_instance = None
            is_internal = False

            try:
                # First try getting as BaseTool (internal wrapper)
                # This might raise ToolNotFoundError if not found
                tool_instance = self.registry.get_tool(tool_name)
                is_internal = True
            except Exception:
                # Maybe it's a dynamic LangChain tool (like MCP)
                tool_instance = self.registry.get_mcp_tool(tool_name)
                is_internal = False

            if not tool_instance:
                 return ToolResult(
                    data=f"Error: Tool {tool_name} not found.",
                    error="Tool not found",
                    success=False
                )

            # 2. Permission Check (only for internal tools that support it)
            if is_internal and agent_permissions:
                if not tool_instance.validate_permissions(agent_permissions):
                    return ToolResult(
                        data=f"Error: Permission denied for tool {tool_name}.",
                        error="Permission denied",
                        success=False
                    )

            # 3. Execution with Timeout
            # We need to distinguish between our BaseTool and LangChain BaseTool
            if is_internal:
                # It's our BaseTool wrapper
                 # BaseTool.execute returns ToolResult
                 result = await asyncio.wait_for(
                    tool_instance.execute(**tool_args),
                    timeout=timeout
                )
                 return result
            else:
                # It's a LangChain BaseTool (e.g. MCP)
                # We need to run it and wrap result
                try:
                    output = await asyncio.wait_for(
                        tool_instance.ainvoke(tool_args),
                        timeout=timeout
                    )
                    return ToolResult(
                        data=str(output),
                        success=True
                    )
                except Exception as e:
                     return ToolResult(
                        data=f"Error executing tool {tool_name}: {e}",
                        error=str(e),
                        success=False
                    )

        except asyncio.TimeoutError:
            return ToolResult(
                data=f"Error: Tool {tool_name} timed out after {timeout}s.",
                error="Timeout",
                success=False
            )
        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return ToolResult(
                data=f"Error: {e}",
                error=str(e),
                success=False
            )
