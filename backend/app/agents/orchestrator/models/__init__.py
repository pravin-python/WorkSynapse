"""
Agent Orchestrator Models
=========================

Database models and Pydantic schemas for the Agent Orchestrator.
"""

from app.agents.orchestrator.models.agent_model import (
    OrchestratorAgent,
    OrchestratorConversation,
    AgentExecution,
)
# AgentConversation (for CustomAgent chats) is in app.models.agent_chat.model
# OrchestratorConversation (for OrchestratorAgent) is in agent_model above
from app.agents.orchestrator.models.schemas import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentListResponse,
    ConversationCreate,
    ConversationResponse,
    ExecutionRequest,
    ExecutionResponse,
    ChatMessage,
    ToolConfig,
    LLMProviderEnum,
    MemoryTypeEnum,
)

__all__ = [
    # SQLAlchemy models
    "OrchestratorAgent",
    "OrchestratorConversation",
    "AgentExecution",
    # Pydantic schemas
    "AgentCreate",
    "AgentUpdate",
    "AgentResponse",
    "AgentListResponse",
    "ConversationCreate",
    "ConversationResponse",
    "ExecutionRequest",
    "ExecutionResponse",
    "ChatMessage",
    "ToolConfig",
    "LLMProviderEnum",
    "MemoryTypeEnum",
]
