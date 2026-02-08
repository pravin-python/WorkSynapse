"""
Agent Orchestrator Core
=======================

Main orchestrator for dynamic agent execution using LangGraph.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, AsyncIterator
from uuid import UUID as UUIDType

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel

from app.agents.orchestrator.config import get_orchestrator_config, OrchestratorConfig
from app.agents.orchestrator.llm import LLMRouter, get_llm_router, LLMResponse
from app.agents.orchestrator.tools import ToolRegistry, get_tool_registry
from app.agents.orchestrator.memory import MemoryManager, get_memory_manager
from app.agents.orchestrator.exceptions import (
    OrchestratorError,
    AgentNotFoundError,
    PromptInjectionError,
    PermissionDeniedError,
    GraphExecutionError,
)
from app.agents.orchestrator.security import SecurityGuard, get_security_guard

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """State for agent execution graph."""

    messages: List[BaseMessage] = []
    agent_id: int = 0
    thread_id: str = ""
    current_step: str = "start"
    tool_results: List[Dict[str, Any]] = []
    iteration: int = 0
    max_iterations: int = 10
    should_stop: bool = False


class ExecutionResult(BaseModel):
    """Result of agent execution."""

    response: str
    tool_calls: List[Dict[str, Any]] = []
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    duration_ms: int = 0
    thread_id: str = ""
    steps: List[str] = []


class AgentOrchestrator:
    """
    Main orchestrator for dynamic agent execution.

    Creates and manages LangGraph-powered agents with:
    - Dynamic LLM provider routing
    - Tool loading and execution
    - Memory management
    - Security checks
    """

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        llm_router: Optional[LLMRouter] = None,
        tool_registry: Optional[ToolRegistry] = None,
        memory_manager: Optional[MemoryManager] = None,
        security_guard: Optional["SecurityGuard"] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            config: Orchestrator configuration
            llm_router: LLM router instance
            tool_registry: Tool registry instance
            memory_manager: Memory manager instance
            security_guard: Security guard instance
        """
        self.config = config or get_orchestrator_config()
        self.llm_router = llm_router or get_llm_router()
        self.tool_registry = tool_registry or get_tool_registry()
        self.memory_manager = memory_manager or get_memory_manager()
        self.security_guard = security_guard or get_security_guard()
        
        # Checkpointer for state persistence
        self._checkpointer = MemorySaver()
        
        # Cache for compiled graphs
        self._graphs: Dict[int, StateGraph] = {}

    async def run(
        self,
        agent_config: Dict[str, Any],
        message: str,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Run an agent with a message.

        Args:
            agent_config: Agent configuration dictionary
            message: User message
            thread_id: Optional thread ID for context
            metadata: Optional execution metadata

        Returns:
            ExecutionResult with response and metrics
        """
        start_time = time.time()
        agent_id = agent_config.get("id", 0)
        thread_id = thread_id or str(uuid.uuid4())
        steps = []

        try:
            # Security check on input
            if not self.security_guard.validate_input(message, agent_config):
                raise PromptInjectionError()

            steps.append("security_check")

            # Build system prompt
            system_prompt = await self._build_system_prompt(agent_config, thread_id)
            steps.append("build_prompt")

            # Get conversation history
            history = await self.memory_manager.get_conversation_history(
                agent_id, thread_id, as_langchain=True
            )
            steps.append("load_history")

            # Build messages
            messages = [SystemMessage(content=system_prompt)]
            messages.extend(history)
            messages.append(HumanMessage(content=message))

            # Get LLM
            provider = agent_config.get("llm_provider", "openai")
            model = agent_config.get("model_name", "gpt-4o")
            llm = self.llm_router.get_langchain_model(provider, model)
            steps.append("load_llm")

            # Load tools
            tool_configs = agent_config.get("tools", [])
            tool_names = [
                t.get("name") if isinstance(t, dict) else t
                for t in tool_configs
            ]
            permissions = agent_config.get("permissions", {})
            allowed_tools = self.tool_registry.validate_tools_for_agent(
                tool_names, permissions
            )
            langchain_tools = self.tool_registry.get_langchain_tools(allowed_tools)
            steps.append("load_tools")

            # Bind tools to LLM
            if langchain_tools:
                llm_with_tools = llm.bind_tools(langchain_tools)
            else:
                llm_with_tools = llm

            # Create and run graph
            graph = self._build_graph(llm_with_tools, langchain_tools)
            steps.append("build_graph")

            # Execute
            config = {
                "configurable": {
                    "thread_id": thread_id,
                },
            }

            # Initial state
            state = {
                "messages": messages,
            }

            # Run the graph
            result = await graph.ainvoke(state, config)
            steps.append("execute_graph")

            # Extract response
            final_messages = result.get("messages", [])
            response_content = ""
            tool_calls = []

            for msg in reversed(final_messages):
                if isinstance(msg, AIMessage):
                    response_content = msg.content if isinstance(msg.content, str) else ""
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        tool_calls = [
                            {"name": tc.get("name", ""), "args": tc.get("args", {})}
                            for tc in msg.tool_calls
                        ]
                    break

            # Store in conversation memory
            await self.memory_manager.add_to_conversation(
                agent_id, thread_id, "user", message
            )
            await self.memory_manager.add_to_conversation(
                agent_id, thread_id, "assistant", response_content
            )
            steps.append("store_memory")

            duration_ms = int((time.time() - start_time) * 1000)

            return ExecutionResult(
                response=response_content,
                tool_calls=tool_calls,
                duration_ms=duration_ms,
                thread_id=thread_id,
                steps=steps,
            )

        except PromptInjectionError:
            raise
        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            raise GraphExecutionError("run", str(e))

    async def stream(
        self,
        agent_config: Dict[str, Any],
        message: str,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream an agent response.

        Args:
            agent_config: Agent configuration dictionary
            message: User message
            thread_id: Optional thread ID
            metadata: Optional metadata

        Yields:
            Stream chunks with type and content
        """
        agent_id = agent_config.get("id", 0)
        thread_id = thread_id or str(uuid.uuid4())

        try:
            # Security check
            if not self.security_guard.validate_input(message, agent_config):
                yield {"type": "error", "error": "Prompt injection detected"}
                return

            yield {"type": "step", "step": "Starting agent..."}

            # Build system prompt
            system_prompt = await self._build_system_prompt(agent_config, thread_id)

            # Get conversation history
            history = await self.memory_manager.get_conversation_history(
                agent_id, thread_id, as_langchain=True
            )

            # Build messages
            messages = [SystemMessage(content=system_prompt)]
            messages.extend(history)
            messages.append(HumanMessage(content=message))

            # Get LLM
            provider = agent_config.get("llm_provider", "openai")
            model = agent_config.get("model_name", "gpt-4o")
            llm = self.llm_router.get_langchain_model(provider, model)

            # Load tools
            tool_configs = agent_config.get("tools", [])
            tool_names = [
                t.get("name") if isinstance(t, dict) else t
                for t in tool_configs
            ]
            permissions = agent_config.get("permissions", {})
            allowed_tools = self.tool_registry.validate_tools_for_agent(
                tool_names, permissions
            )
            langchain_tools = self.tool_registry.get_langchain_tools(allowed_tools)

            if langchain_tools:
                llm_with_tools = llm.bind_tools(langchain_tools)
            else:
                llm_with_tools = llm

            # Build graph
            graph = self._build_graph(llm_with_tools, langchain_tools)

            config = {
                "configurable": {"thread_id": thread_id},
            }
            state = {"messages": messages}

            yield {"type": "step", "step": "Generating response..."}

            # Stream the graph
            full_response = ""
            async for event in graph.astream_events(state, config, version="v2"):
                kind = event.get("event", "")
                
                if kind == "on_chat_model_stream":
                    data = event.get("data", {})
                    chunk = data.get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        full_response += chunk.content
                        yield {"type": "token", "content": chunk.content}
                
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    yield {"type": "tool_start", "tool": tool_name}
                
                elif kind == "on_tool_end":
                    tool_name = event.get("name", "")
                    output = event.get("data", {}).get("output", "")
                    yield {"type": "tool_end", "tool": tool_name, "result": str(output)[:500]}

            # Store in memory
            await self.memory_manager.add_to_conversation(
                agent_id, thread_id, "user", message
            )
            await self.memory_manager.add_to_conversation(
                agent_id, thread_id, "assistant", full_response
            )

            yield {"type": "done", "thread_id": thread_id}

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield {"type": "error", "error": str(e)}

    async def _build_system_prompt(self, agent_config: Dict[str, Any], thread_id: str = "", message: str = "") -> str:
        """
        Build the complete system prompt for an agent.
        Supports both legacy configuration and new structured prompt templates.
        """
        # Check for structured prompt template
        if "prompt_template" in agent_config and agent_config["prompt_template"]:
            return await self._build_structured_system_prompt(agent_config, thread_id, message)

        # Legacy Prompt Building
        parts = []

        # Base system prompt
        system_prompt = agent_config.get("system_prompt", "")
        if system_prompt:
            parts.append(system_prompt)

        # Identity guidance
        identity = agent_config.get("identity_guidance", "")
        if identity:
            parts.append(f"\n\nIdentity:\n{identity}")

        # Goal
        goal = agent_config.get("goal", "")
        if goal:
            parts.append(f"\n\nGoal:\n{goal}")

        # Capabilities
        tools = agent_config.get("tools", [])
        if tools:
            tool_names = [
                t.get("name") if isinstance(t, dict) else t
                for t in tools
            ]
            parts.append(f"\n\nAvailable tools: {', '.join(tool_names)}")

        return "\n".join(parts)

    async def _build_structured_system_prompt(self, agent_config: Dict[str, Any], thread_id: str, message: str) -> str:
        """
        Build a LangChain-style structured prompt from templates.
        """
        # 1. Get Template Parts
        # Try to get from config first (runtime override), then fall back to DB/Defaults
        template = agent_config.get("prompt_template", {})
        
        system_part = template.get("system_prompt", "") or agent_config.get("system_prompt", "")
        goal_part = template.get("goal_prompt", "")
        instruction_part = template.get("instruction_prompt", "")
        output_part = template.get("output_prompt", "")
        tool_part = template.get("tool_prompt", "")

        # 2. Dynamic Runtime Data
        context_part = ""
        memory_part = ""
        scratchpad_part = ""
        user_prompt = message
        task_prompt = "Interact with the user to help them achieve their goals."

        # RAG Integration (Context)
        if message:
            try:
                from app.ai.rag.rag_service import get_rag_service
                rag_service = get_rag_service()
                # Get relevant chunks
                chunks = await rag_service.retrieve_context(message, k=5)
                if chunks:
                    context_part = "\n---\n".join(chunks)
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
        
        # Memory Integration
        if thread_id:
            try:
                agent_id = agent_config.get("id", 0)
                # Get session memory summary or last K messages if needed explicitly here
                # Note: The conversation history is usually appended as messages list in LangChain
                # This 'memory_prompt' section is for specific summarized context
                session_mem = self.memory_manager.get_session_memory(agent_id, thread_id)
                session_data = session_mem.get_all()
                if session_data:
                    memory_items = [f"{k}: {v}" for k, v in session_data.items()]
                    memory_part = "\n".join(memory_items)
            except Exception as e:
                logger.warning(f"Failed to load session memory: {e}")

        # Tools Default Description
        if not tool_part:
            tools = agent_config.get("tools", [])
            if tools:
                tool_names = [t.get("name") if isinstance(t, dict) else t for t in tools]
                tool_part = f"Available Tools: {', '.join(tool_names)}"

        # 3. Assemble Prompt
        # This matches the requested format in the prompt
        assembled_prompt = f"""
{system_part}

GOAL:
{goal_part}

INSTRUCTIONS:
{instruction_part}

TOOLS:
{tool_part}

CONTEXT:
{context_part}

MEMORY:
{memory_part}

SCRATCHPAD:
{scratchpad_part}

USER:
{user_prompt}

TASK:
{task_prompt}

OUTPUT FORMAT:
{output_part}
"""
        return assembled_prompt.strip()

    def _build_graph(self, llm, tools):
        """Build the LangGraph execution graph."""
        from langgraph.graph import StateGraph
        from langgraph.graph.message import add_messages
        from typing import Annotated

        class GraphState(BaseModel):
            messages: Annotated[list, add_messages]

        # Define the agent node
        async def agent_node(state: GraphState):
            response = await llm.ainvoke(state.messages)
            return {"messages": [response]}

        # Build graph
        builder = StateGraph(GraphState)
        builder.add_node("agent", agent_node)

        if tools:
            tool_node = ToolNode(tools=tools)
            builder.add_node("tools", tool_node)
            
            builder.add_edge(START, "agent")
            builder.add_conditional_edges(
                "agent",
                tools_condition,
            )
            builder.add_edge("tools", "agent")
        else:
            builder.add_edge(START, "agent")
            builder.add_edge("agent", END)

        return builder.compile(checkpointer=self._checkpointer)

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available LLM providers."""
        return self.llm_router.get_all_providers_info()

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return self.tool_registry.get_tools_info()


# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
