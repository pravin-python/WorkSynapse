"""
WorkSynapse Models Package
==========================
Central import point for all SQLAlchemy models.

This module imports all models to ensure they are registered with SQLAlchemy's
metadata before Alembic migrations are generated.
"""

# Base classes
from app.models.base import Base, TimestampMixin, AuditMixin, generate_uuid

# User & Authentication Models
from app.models.user.model import (
    User,
    UserRole,
    UserStatus,
    Role,
    Permission,
    PermissionAction,
    Session,
    LoginHistory,
    user_roles,
    role_permissions,
)

# Project Management Models
from app.models.project.model import (
    Project,
    ProjectStatus,
    ProjectVisibility,
    ProjectMember,
    MemberRole,
    Board,
    BoardColumn,
    Sprint,
    SprintStatus,
    Milestone,
)

# Task Models
from app.models.task.model import (
    Task,
    TaskStatus,
    TaskPriority,
    TaskType,
    TaskDependency,
    DependencyType,
    Label,
    TaskComment,
    TaskAttachment,
    TimeLog,
    task_labels,
    task_watchers,
)

# Chat Models
from app.models.chat.model import (
    Channel,
    ChannelType,
    Message,
    MessageType,
    MessageReaction,
    MessageFile,
    ReadReceipt,
    PinnedMessage,
    channel_members,
)

# Notes Models
from app.models.note.model import (
    Note,
    NoteFolder,
    NoteShare,
    SharePermission,
    NoteTag,
    note_tag_map,
)

# AI Agent Governance Models
from app.models.agent.model import (
    Agent,
    AgentStatus,
    AgentType,
    LLMProvider,
    LLMModel,
    AgentUserPermission,
    AgentTool,
    AgentSession,
    AgentSessionStatus,
    AgentMessage,
    AgentCall,
    AgentCallStatus,
    AgentAction,
    AgentActionType,
    AgentActionStatus,
    AgentTask,
    AgentCostLog,
    agent_tools,
    agent_role_permissions,
)

# Work Tracking Models
from app.models.worklog.model import (
    WorkLog,
    WorkLogType,
    ActivityLog,
    ActivityType,
    AppUsage,
    IdlePeriod,
    IdlePeriodType,
    ProductivitySummary,
    SecurityAuditLog,
)

# LLM Key Management Models
from app.models.llm.model import (
    LLMKeyProvider,
    LLMKeyProviderType,
    LLMApiKey,
    UserAIAgent,
    UserAgentType,
    UserAgentStatus,
    UserAgentSession,
)

# Agent Builder Models (Custom Agent Creation)
from app.models.agent_builder.model import (
    AgentToolType,
    AgentConnectionType,
    CustomAgentStatus,
    AgentModel,
    AgentApiKey,
    CustomAgent,
    AgentToolConfig,
    AgentConnection,
    AgentMCPServer,
    AgentPromptTemplate,
    AgentRuntimePromptData,
)

# Local AI Models
from app.models.local_models.model import (
    LocalModel,
    ModelDownloadLog,
    ModelSource,
    ModelStatus,
    ModelType,
)

# RAG Knowledge Models
from app.models.rag import (
    RagDocument,
    RagChunk,
    AgentRagDocument,
)

# Agent Chat Models (AI agent conversations)
from app.models.agent_chat.model import (
    AgentConversation,
    AgentChatMessage,
    AgentChatFile,
    AgentChatSenderType,
    AgentChatMessageType,
)

# Agent Orchestrator Models
from app.agents.orchestrator.models import (
    OrchestratorAgent,
    OrchestratorConversation,
    AgentExecution,
)


# All models for Alembic autogenerate
__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "AuditMixin",
    "generate_uuid",
    
    # User
    "User",
    "UserRole",
    "UserStatus",
    "Role",
    "Permission",
    "PermissionAction",
    "Session",
    "LoginHistory",
    "user_roles",
    "role_permissions",
    
    # Project
    "Project",
    "ProjectStatus",
    "ProjectVisibility",
    "ProjectMember",
    "MemberRole",
    "Board",
    "BoardColumn",
    "Sprint",
    "SprintStatus",
    "Milestone",
    
    # Task
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskType",
    "TaskDependency",
    "DependencyType",
    "Label",
    "TaskComment",
    "TaskAttachment",
    "TimeLog",
    "task_labels",
    "task_watchers",
    
    # Chat
    "Channel",
    "ChannelType",
    "Message",
    "MessageType",
    "MessageReaction",
    "MessageFile",
    "ReadReceipt",
    "PinnedMessage",
    "channel_members",
    
    # Notes
    "Note",
    "NoteFolder",
    "NoteShare",
    "SharePermission",
    "NoteTag",
    "note_tag_map",
    
    # Agent
    "Agent",
    "AgentStatus",
    "AgentType",
    "LLMProvider",
    "LLMModel",
    "AgentUserPermission",
    "AgentTool",
    "AgentSession",
    "AgentSessionStatus",
    "AgentMessage",
    "AgentCall",
    "AgentCallStatus",
    "AgentAction",
    "AgentActionType",
    "AgentActionStatus",
    "AgentTask",
    "AgentCostLog",
    "agent_tools",
    "agent_role_permissions",
    
    # WorkLog
    "WorkLog",
    "WorkLogType",
    "ActivityLog",
    "ActivityType",
    "AppUsage",
    "IdlePeriod",
    "IdlePeriodType",
    "ProductivitySummary",
    "SecurityAuditLog",
    
    # Agent Builder
    "AgentToolType",
    "AgentConnectionType",
    "CustomAgentStatus",
    "AgentModel",
    "AgentApiKey",
    "CustomAgent",
    "AgentToolConfig",
    "AgentConnection",
    "AgentMCPServer",
    "AgentPromptTemplate",
    "AgentRuntimePromptData",
    "AgentMCPServer",

    # Local Models
    "LocalModel",
    "ModelDownloadLog",
    "ModelSource",
    "ModelStatus",
    "ModelType",
    
    # RAG
    "RagDocument",
    "RagChunk",
    "AgentRagDocument",

    # Agent Chat
    "AgentConversation",
    "AgentChatMessage",
    "AgentChatFile",
    "AgentChatSenderType",
    "AgentChatMessageType",

    # Orchestrator
    "OrchestratorAgent",
    "OrchestratorConversation",
    "AgentExecution",
]
