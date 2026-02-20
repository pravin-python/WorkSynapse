"""
Tool Tester
===========

Test tools functionality.
"""

from typing import Dict, Any, Optional
from app.agents.tools.tool_registry import get_tool_registry
from app.agents.tools.tool_executor import ToolExecutor

class ToolTester:
    """
    Test agent tools.
    """

    async def test_tool(self, tool_name: str, args: Dict[str, Any], permissions: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """
        Run a tool with test arguments.
        """
        registry = get_tool_registry()
        executor = ToolExecutor(registry)

        # If testing, usually we want to bypass permission checks or pass minimal ones
        # But we allow passing permissions

        result = await executor.execute(tool_name, args, agent_permissions=permissions)
        return result.model_dump()
