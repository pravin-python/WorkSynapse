"""
WorkSynapse Agent Chat Service
================================
Business logic for agent conversations, messages, and file uploads.
"""

import logging
import os
import uuid
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.agent_chat.model import (
    AgentConversation,
    AgentChatMessage,
    AgentChatFile,
    AgentChatSenderType,
    AgentChatMessageType,
)
from app.models.agent_builder.model import CustomAgent

logger = logging.getLogger(__name__)

# File upload configuration
UPLOAD_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "media", "chat_uploads"
)

ALLOWED_FILE_TYPES = {
    # Images
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
    # Documents
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain", "text/csv", "text/markdown",
    # Code
    "application/json", "application/xml",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class AgentChatServiceError(Exception):
    """Custom exception for agent chat service errors."""
    pass


class AgentChatService:
    """Service for agent chat operations."""

    # =========================================================================
    # CONVERSATIONS
    # =========================================================================

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        agent_id: int,
        user_id: int,
        title: Optional[str] = None,
    ) -> AgentConversation:
        """Create a new conversation with an agent."""
        # Verify agent exists and user has access
        agent = await db.get(CustomAgent, agent_id)
        if not agent:
            raise AgentChatServiceError(f"Agent {agent_id} not found")
        if not agent.is_public and agent.created_by_user_id != user_id:
            raise AgentChatServiceError("You don't have access to this agent")

        conversation = AgentConversation(
            agent_id=agent_id,
            user_id=user_id,
            title=title or f"Chat with {agent.name}",
            thread_id=str(uuid.uuid4()),
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        logger.info(f"Created conversation {conversation.id} for agent {agent_id} by user {user_id}")
        return conversation

    @staticmethod
    async def get_conversations(
        db: AsyncSession,
        agent_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Get paginated list of conversations for a specific agent."""
        conditions = [
            AgentConversation.agent_id == agent_id,
            AgentConversation.user_id == user_id,
            AgentConversation.is_deleted == False,
            AgentConversation.is_archived == False,
        ]

        # Count
        count_query = select(func.count()).select_from(AgentConversation).where(and_(*conditions))
        total = (await db.execute(count_query)).scalar() or 0

        # Fetch
        query = (
            select(AgentConversation)
            .where(and_(*conditions))
            .order_by(desc(AgentConversation.last_message_at.is_(None)), desc(AgentConversation.last_message_at), desc(AgentConversation.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(query)
        conversations = result.scalars().unique().all()

        return {
            "conversations": conversations,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": total > page * page_size,
        }

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
    ) -> AgentConversation:
        """Get a single conversation with access check."""
        query = (
            select(AgentConversation)
            .options(joinedload(AgentConversation.agent))
            .where(
                AgentConversation.id == conversation_id,
                AgentConversation.is_deleted == False,
            )
        )
        result = await db.execute(query)
        conversation = result.scalars().first()

        if not conversation:
            raise AgentChatServiceError("Conversation not found")
        if conversation.user_id != user_id:
            raise AgentChatServiceError("Access denied")

        return conversation

    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
    ) -> None:
        """Soft delete a conversation."""
        conversation = await AgentChatService.get_conversation(db, conversation_id, user_id)
        conversation.soft_delete()
        await db.commit()

    # =========================================================================
    # MESSAGES
    # =========================================================================

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Get paginated messages for a conversation."""
        # Access check
        await AgentChatService.get_conversation(db, conversation_id, user_id)

        conditions = [
            AgentChatMessage.conversation_id == conversation_id,
            AgentChatMessage.is_deleted == False,
        ]

        # Count
        count_query = select(func.count()).select_from(AgentChatMessage).where(and_(*conditions))
        total = (await db.execute(count_query)).scalar() or 0

        # Fetch with files
        query = (
            select(AgentChatMessage)
            .options(selectinload(AgentChatMessage.files))
            .where(and_(*conditions))
            .order_by(AgentChatMessage.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(query)
        messages = result.scalars().unique().all()

        return {
            "messages": messages,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": total > page * page_size,
        }

    @staticmethod
    async def create_user_message(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        content: str,
        message_type: str = "text",
        file_ids: Optional[List[int]] = None,
    ) -> AgentChatMessage:
        """Save a user message to the conversation."""
        # Access check
        conversation = await AgentChatService.get_conversation(db, conversation_id, user_id)

        message = AgentChatMessage(
            conversation_id=conversation_id,
            sender_type=AgentChatSenderType.USER,
            content=content,
            message_type=AgentChatMessageType(message_type),
        )
        db.add(message)
        await db.flush()  # Get the message ID

        # Link uploaded files to this message
        if file_ids:
            for file_id in file_ids:
                file_query = select(AgentChatFile).where(
                    AgentChatFile.id == file_id,
                    AgentChatFile.conversation_id == conversation_id,
                    AgentChatFile.uploaded_by_user_id == user_id,
                )
                file_result = await db.execute(file_query)
                chat_file = file_result.scalars().first()
                if chat_file:
                    chat_file.message_id = message.id

        # Update conversation
        conversation.last_message_at = datetime.now(timezone.utc)
        conversation.message_count += 1

        # Auto-generate title from first message
        if conversation.message_count == 1:
            conversation.title = content[:100] + ("..." if len(content) > 100 else "")

        await db.commit()
        await db.refresh(message)

        return message

    @staticmethod
    async def save_agent_message(
        db: AsyncSession,
        conversation_id: int,
        content: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        tokens_total: int = 0,
        duration_ms: int = 0,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> AgentChatMessage:
        """Save an agent response message."""
        message = AgentChatMessage(
            conversation_id=conversation_id,
            sender_type=AgentChatSenderType.AGENT,
            content=content,
            message_type=AgentChatMessageType.TEXT,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_total,
            duration_ms=duration_ms,
            tool_calls=tool_calls,
        )
        db.add(message)

        # Update conversation stats
        conv_query = select(AgentConversation).where(AgentConversation.id == conversation_id)
        result = await db.execute(conv_query)
        conversation = result.scalars().first()
        if conversation:
            conversation.last_message_at = datetime.now(timezone.utc)
            conversation.message_count += 1
            conversation.total_tokens_used += tokens_total

        await db.commit()
        await db.refresh(message)

        return message

    # =========================================================================
    # FILE UPLOADS
    # =========================================================================

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize a filename, keeping only safe characters."""
        name, ext = os.path.splitext(filename)
        name = re.sub(r'[^\w\-.]', '_', name)
        return f"{name}_{uuid.uuid4().hex[:8]}{ext}"

    @staticmethod
    async def upload_file(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        file_name: str,
        file_content: bytes,
        content_type: str,
    ) -> AgentChatFile:
        """Upload and save a file for a conversation."""
        # Validate file type
        if content_type not in ALLOWED_FILE_TYPES:
            raise AgentChatServiceError(f"File type '{content_type}' is not allowed")

        # Validate file size
        file_size = len(file_content)
        if file_size > MAX_FILE_SIZE:
            raise AgentChatServiceError(f"File size exceeds maximum of {MAX_FILE_SIZE // (1024*1024)}MB")

        # Create upload directory
        upload_dir = os.path.join(UPLOAD_BASE_DIR, str(conversation_id))
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        safe_name = AgentChatService._sanitize_filename(file_name)
        file_path = os.path.join(upload_dir, safe_name)

        with open(file_path, "wb") as f:
            f.write(file_content)

        # Relative path for DB storage
        relative_path = f"media/chat_uploads/{conversation_id}/{safe_name}"

        # Create DB record
        chat_file = AgentChatFile(
            conversation_id=conversation_id,
            uploaded_by_user_id=user_id,
            file_name=safe_name,
            original_file_name=file_name,
            file_path=relative_path,
            file_type=content_type,
            file_size=file_size,
        )
        db.add(chat_file)
        await db.commit()
        await db.refresh(chat_file)

        logger.info(f"Uploaded file {safe_name} ({file_size} bytes) for conversation {conversation_id}")
        return chat_file

    @staticmethod
    async def get_file(
        db: AsyncSession,
        file_id: int,
        user_id: int,
    ) -> AgentChatFile:
        """Get a file with access check."""
        query = (
            select(AgentChatFile)
            .join(AgentConversation, AgentChatFile.conversation_id == AgentConversation.id)
            .where(
                AgentChatFile.id == file_id,
                AgentConversation.user_id == user_id,
            )
        )
        result = await db.execute(query)
        chat_file = result.scalars().first()

        if not chat_file:
            raise AgentChatServiceError("File not found or access denied")
        return chat_file

    # =========================================================================
    # AGENT CONFIG BUILDER
    # =========================================================================

    @staticmethod
    async def build_agent_config(
        db: AsyncSession,
        agent_id: int,
    ) -> Dict[str, Any]:
        """Build the agent configuration dict needed by the orchestrator."""
        from sqlalchemy.orm import joinedload, selectinload
        from app.models.agent_builder.model import AgentModel

        query = (
            select(CustomAgent)
            .options(
                joinedload(CustomAgent.model).joinedload(AgentModel.provider),
                joinedload(CustomAgent.local_model),
                joinedload(CustomAgent.api_key),
                selectinload(CustomAgent.tools),
                selectinload(CustomAgent.connections),
                selectinload(CustomAgent.mcp_servers),
            )
            .where(CustomAgent.id == agent_id)
        )
        result = await db.execute(query)
        agent = result.scalars().first()

        if not agent:
            raise AgentChatServiceError(f"Agent {agent_id} not found")

        # Build config
        config = {
            "id": agent.id,
            "name": agent.name,
            "system_prompt": agent.system_prompt,
            "goal_prompt": agent.goal_prompt,
            "service_prompt": agent.service_prompt,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "top_p": agent.top_p,
            "frequency_penalty": agent.frequency_penalty,
            "presence_penalty": agent.presence_penalty,
            "action_mode_enabled": agent.action_mode_enabled,
            "autonomy_level": agent.autonomy_level.value if agent.autonomy_level else "low",
            "max_steps": agent.max_steps,
            "mcp_enabled": agent.mcp_enabled,
            "memory_enabled": agent.memory_enabled,
            "rag_enabled": agent.rag_enabled,
        }

        # LLM config
        if agent.model:
            provider = agent.model.provider
            config["llm_provider"] = provider.name if provider else "openai"
            config["model_name"] = agent.model.name
        elif agent.local_model:
            config["llm_provider"] = "ollama"
            config["model_name"] = agent.local_model.name

        # API key
        if agent.api_key:
            config["api_key"] = agent.api_key.encrypted_key

        # Tools
        config["tools"] = [
            {"name": t.tool_name, "type": t.tool_type.value, "config": t.config_json}
            for t in agent.tools if t.is_enabled
        ]

        # MCP servers
        config["mcp_servers"] = [
            {
                "server_url": s.server_url,
                "server_name": s.server_name,
                "config": s.config_json,
                "encrypted_auth": s.auth_credentials,
            }
            for s in agent.mcp_servers if s.is_enabled
        ]

        return config
