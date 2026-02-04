"""
Custom exceptions for the Agent Orchestrator.
"""


class OrchestratorError(Exception):
    """Base exception for all orchestrator errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AgentNotFoundError(OrchestratorError):
    """Raised when an agent cannot be found."""

    def __init__(self, agent_id: str | int):
        super().__init__(f"Agent not found: {agent_id}", {"agent_id": agent_id})
        self.agent_id = agent_id


class AgentConfigurationError(OrchestratorError):
    """Raised when agent configuration is invalid."""

    def __init__(self, message: str, agent_id: str | int = None):
        super().__init__(message, {"agent_id": agent_id})
        self.agent_id = agent_id


class ToolNotFoundError(OrchestratorError):
    """Raised when a tool cannot be found or loaded."""

    def __init__(self, tool_name: str):
        super().__init__(f"Tool not found: {tool_name}", {"tool_name": tool_name})
        self.tool_name = tool_name


class ToolExecutionError(OrchestratorError):
    """Raised when a tool fails to execute."""

    def __init__(self, tool_name: str, error: str):
        super().__init__(
            f"Tool execution failed: {tool_name} - {error}",
            {"tool_name": tool_name, "error": error},
        )
        self.tool_name = tool_name
        self.error = error


class LLMProviderError(OrchestratorError):
    """Raised when there's an issue with the LLM provider."""

    def __init__(self, provider: str, error: str):
        super().__init__(
            f"LLM provider error ({provider}): {error}",
            {"provider": provider, "error": error},
        )
        self.provider = provider
        self.error = error


class LLMProviderNotFoundError(LLMProviderError):
    """Raised when an LLM provider is not available."""

    def __init__(self, provider: str):
        super().__init__(provider, f"Provider not available: {provider}")


class MemoryError(OrchestratorError):
    """Raised when there's an issue with the memory system."""

    def __init__(self, memory_type: str, error: str):
        super().__init__(
            f"Memory error ({memory_type}): {error}",
            {"memory_type": memory_type, "error": error},
        )
        self.memory_type = memory_type
        self.error = error


class PermissionDeniedError(OrchestratorError):
    """Raised when an action is not permitted."""

    def __init__(self, action: str, resource: str, reason: str = None):
        message = f"Permission denied: {action} on {resource}"
        if reason:
            message += f" - {reason}"
        super().__init__(
            message, {"action": action, "resource": resource, "reason": reason}
        )
        self.action = action
        self.resource = resource
        self.reason = reason


class PromptInjectionError(OrchestratorError):
    """Raised when a potential prompt injection is detected."""

    def __init__(self, detected_pattern: str = None):
        message = "Potential prompt injection detected"
        super().__init__(message, {"detected_pattern": detected_pattern})
        self.detected_pattern = detected_pattern


class RateLimitExceededError(OrchestratorError):
    """Raised when rate limit is exceeded."""

    def __init__(self, limit: int, window_seconds: int, resource: str = "agent"):
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window_seconds}s for {resource}",
            {"limit": limit, "window_seconds": window_seconds, "resource": resource},
        )
        self.limit = limit
        self.window_seconds = window_seconds
        self.resource = resource


class GraphExecutionError(OrchestratorError):
    """Raised when the LangGraph execution fails."""

    def __init__(self, step: str, error: str):
        super().__init__(
            f"Graph execution failed at {step}: {error}",
            {"step": step, "error": error},
        )
        self.step = step
        self.error = error
