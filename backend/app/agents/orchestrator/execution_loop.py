"""
Execution Loop
==============

Core agent execution loop using LangGraph.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, AsyncIterator, Annotated, TypedDict
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from app.agents.providers.provider_router import ProviderRouter
from app.agents.tools.tool_registry import ToolRegistry, get_tool_registry
from app.agents.prompts.prompt_builder import PromptBuilder
from app.agents.memory.memory_manager import MemoryManager, get_memory_manager
from app.services.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]

class ExecutionLoop:
    """
    Core agent execution loop using LangGraph.
    """

    def __init__(
        self,
        agent_config: Dict[str, Any],
        memory_manager: Optional[MemoryManager] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        self.config = agent_config
        self.memory_manager = memory_manager or get_memory_manager()
        self.tool_registry = tool_registry or get_tool_registry()
        self.checkpointer = MemorySaver()

    async def run(
        self,
        message: str,
        thread_id: str,
        agent_id: int
    ) -> Dict[str, Any]:
        """
        Run the execution loop.
        """
        # 1. Setup LLM
        provider_name = self.config.get("llm_provider", "openai")
        model_name = self.config.get("model_name", "gpt-4o")

        try:
            llm = ProviderRouter().get_langchain_model(provider_name, model_name)
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")
            raise

        # 2. Setup Tools
        tool_configs = self.config.get("tools", [])
        tool_names = [t.get("name") if isinstance(t, dict) else t for t in tool_configs]
        permissions = self.config.get("permissions", {})

        # Load MCP Tools
        mcp_servers = self.config.get("mcp_servers", [])
        if self.config.get("mcp_enabled", False) and mcp_servers:
            for server in mcp_servers:
                try:
                    client = MCPClient(
                        server_url=server.get("server_url"),
                        auth_token=server.get("encrypted_auth")
                    )
                    mcp_tools = await client.list_tools()
                    self.tool_registry.register_mcp_tools(client, mcp_tools)

                    for t in mcp_tools:
                        if t.name not in tool_names:
                            tool_names.append(t.name)
                except Exception as e:
                    logger.warning(f"Failed to load MCP tools from server: {e}")

        allowed_tools = self.tool_registry.validate_tools_for_agent(tool_names, permissions)
        langchain_tools = self.tool_registry.get_langchain_tools(allowed_tools)

        if langchain_tools:
            llm = llm.bind_tools(langchain_tools)

        # 3. Build Prompt
        prompt_builder = PromptBuilder(self.config)
        history = await self.memory_manager.get_conversation_history(agent_id, thread_id, as_langchain=True)
        initial_messages = await prompt_builder.build_messages(message, conversation_history=history)

        # 4. Construct Graph
        workflow = StateGraph(GraphState)

        async def agent_node(state: GraphState):
            response = await llm.ainvoke(state["messages"])
            return {"messages": [response]}

        workflow.add_node("agent", agent_node)

        if langchain_tools:
            tool_node = ToolNode(langchain_tools)
            workflow.add_node("tools", tool_node)

            workflow.add_edge(START, "agent")
            workflow.add_conditional_edges("agent", tools_condition)
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge(START, "agent")
            workflow.add_edge("agent", END)

        app = workflow.compile(checkpointer=self.checkpointer)

        # 5. Execute Graph
        graph_thread_id = str(uuid.uuid4())

        config = {
            "configurable": {"thread_id": graph_thread_id},
            "recursion_limit": self.config.get("max_steps", 10) + 1
        }

        final_state = await app.ainvoke({"messages": initial_messages}, config)

        # 6. Extract Result
        last_message = final_state["messages"][-1]
        response_content = last_message.content if isinstance(last_message.content, str) else ""

        return {
            "response": response_content,
            "tool_calls": getattr(last_message, "tool_calls", []),
            "messages": final_state["messages"]
        }
