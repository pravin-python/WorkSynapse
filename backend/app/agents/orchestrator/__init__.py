"""
WorkSynapse Agent Orchestrator
=============================

Dynamic AI agent creation platform using LangChain and LangGraph.

This module provides:
- Dynamic agent creation from database configuration
- Multi-LLM provider routing (OpenAI, Ollama, Gemini, Claude, HuggingFace)
- MCP tool integration (GitHub, Slack, Teams, Telegram)
- Memory management (conversation, vector, session)
- LangGraph-powered multi-step planning
- Security features (prompt injection protection, permissions)
"""

from app.agents.orchestrator.orchestrator import AgentOrchestrator, get_orchestrator, ExecutionResult
from app.agents.orchestrator.config import OrchestratorConfig, get_orchestrator_config
from app.agents.orchestrator.security import SecurityGuard, get_security_guard
from app.agents.orchestrator.exceptions import (
    OrchestratorError,
    AgentNotFoundError,
    AgentConfigurationError,
    ToolNotFoundError,
    ToolExecutionError,
    LLMProviderError,
    LLMProviderNotFoundError,
    MemoryError,
    PermissionDeniedError,
    PromptInjectionError,
    RateLimitExceededError,
    GraphExecutionError,
)

__all__ = [
    # Core
    "AgentOrchestrator",
    "get_orchestrator",
    "ExecutionResult",
    # Config
    "OrchestratorConfig",
    "get_orchestrator_config",
    # Security
    "SecurityGuard",
    "get_security_guard",
    # Exceptions
    "OrchestratorError",
    "AgentNotFoundError",
    "AgentConfigurationError",
    "ToolNotFoundError",
    "ToolExecutionError",
    "LLMProviderError",
    "LLMProviderNotFoundError",
    "MemoryError",
    "PermissionDeniedError",
    "PromptInjectionError",
    "RateLimitExceededError",
    "GraphExecutionError",
]
