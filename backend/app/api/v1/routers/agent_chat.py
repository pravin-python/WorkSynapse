"""
WorkSynapse Agent Chat API Router
====================================
REST + SSE endpoints for agent conversations, messages, and file uploads.
"""

import json
import logging
import time
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user.model import User
from app.services.agent_chat_service import AgentChatService, AgentChatServiceError
from app.schemas.agent_chat import (
    ConversationCreate,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    ChatFileResponse,
    FileUploadResponse,
)
from app.agents.orchestrator.core import get_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# CONVERSATIONS
# =============================================================================

@router.post(
    "/agents/{agent_id}/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation with an agent"
)
async def create_conversation(
    agent_id: int,
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new conversation session with a specific agent."""
    try:
        conversation = await AgentChatService.create_conversation(
            db, agent_id, current_user.id, data.title
        )
        return ConversationResponse(
            id=conversation.id,
            agent_id=conversation.agent_id,
            user_id=conversation.user_id,
            title=conversation.title,
            thread_id=conversation.thread_id,
            is_archived=conversation.is_archived,
            last_message_at=conversation.last_message_at,
            message_count=conversation.message_count,
            total_tokens_used=conversation.total_tokens_used,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
    except AgentChatServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/agents/{agent_id}/conversations",
    response_model=ConversationListResponse,
    summary="List conversations for an agent"
)
async def list_conversations(
    agent_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated list of conversations for a specific agent."""
    result = await AgentChatService.get_conversations(
        db, agent_id, current_user.id, page, page_size
    )

    conversations = []
    for conv in result["conversations"]:
        # Get last message preview
        last_preview = None
        if conv.message_count > 0:
            msgs = await AgentChatService.get_messages(db, conv.id, current_user.id, 1, 1)
            if msgs["messages"]:
                last_msg = msgs["messages"][-1]
                last_preview = last_msg.content[:100] + ("..." if len(last_msg.content) > 100 else "")

        conversations.append(ConversationResponse(
            id=conv.id,
            agent_id=conv.agent_id,
            user_id=conv.user_id,
            title=conv.title,
            thread_id=conv.thread_id,
            is_archived=conv.is_archived,
            last_message_at=conv.last_message_at,
            message_count=conv.message_count,
            total_tokens_used=conv.total_tokens_used,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            last_message_preview=last_preview,
        ))

    return ConversationListResponse(
        conversations=conversations,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        has_more=result["has_more"],
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get conversation details"
)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single conversation with agent info."""
    try:
        conv = await AgentChatService.get_conversation(db, conversation_id, current_user.id)
        return ConversationDetailResponse(
            id=conv.id,
            agent_id=conv.agent_id,
            user_id=conv.user_id,
            title=conv.title,
            thread_id=conv.thread_id,
            is_archived=conv.is_archived,
            last_message_at=conv.last_message_at,
            message_count=conv.message_count,
            total_tokens_used=conv.total_tokens_used,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            agent_name=conv.agent.name if conv.agent else None,
            agent_avatar_url=conv.agent.avatar_url if conv.agent else None,
            agent_color=conv.agent.color if conv.agent else None,
        )
    except AgentChatServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation"
)
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a conversation."""
    try:
        await AgentChatService.delete_conversation(db, conversation_id, current_user.id)
    except AgentChatServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# MESSAGES
# =============================================================================

@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageListResponse,
    summary="Get conversation messages"
)
async def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated messages for a conversation."""
    try:
        result = await AgentChatService.get_messages(
            db, conversation_id, current_user.id, page, page_size
        )

        messages = [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender_type=msg.sender_type.value,
                content=msg.content,
                message_type=msg.message_type.value,
                tokens_input=msg.tokens_input,
                tokens_output=msg.tokens_output,
                tokens_total=msg.tokens_total,
                duration_ms=msg.duration_ms,
                tool_calls=msg.tool_calls,
                files=[
                    ChatFileResponse(
                        id=f.id,
                        message_id=f.message_id,
                        conversation_id=f.conversation_id,
                        file_name=f.file_name,
                        original_file_name=f.original_file_name,
                        file_path=f.file_path,
                        file_type=f.file_type,
                        file_size=f.file_size,
                        thumbnail_path=f.thumbnail_path,
                        is_rag_ingested=f.is_rag_ingested,
                        created_at=f.created_at,
                    )
                    for f in msg.files
                ],
                created_at=msg.created_at,
            )
            for msg in result["messages"]
        ]

        return MessageListResponse(
            messages=messages,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            has_more=result["has_more"],
        )
    except AgentChatServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/conversations/{conversation_id}/messages",
    summary="Send a message and stream agent response"
)
async def send_message(
    conversation_id: int,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a user message and stream the agent's response via SSE.
    
    SSE event types:
    - step: Progress update
    - token: Streamed response token
    - tool_start: Tool execution started
    - tool_end: Tool execution completed
    - message: Final user message saved
    - agent_message: Final agent message saved
    - done: Stream complete
    - error: Error occurred
    """
    try:
        # Save user message
        user_message = await AgentChatService.create_user_message(
            db, conversation_id, current_user.id,
            data.content, data.message_type.value, data.file_ids
        )

        # Get conversation for thread_id
        conversation = await AgentChatService.get_conversation(
            db, conversation_id, current_user.id
        )

        # Build agent config
        agent_config = await AgentChatService.build_agent_config(db, conversation.agent_id)

    except AgentChatServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))

    async def event_stream():
        """Generate SSE events."""
        start_time = time.time()
        full_response = ""
        tool_calls_list = []

        try:
            # Send user message confirmation
            yield f"data: {json.dumps({'type': 'message', 'message_id': user_message.id})}\n\n"

            # Get orchestrator and stream
            orchestrator = get_orchestrator()

            async for chunk in orchestrator.stream(
                agent_config=agent_config,
                message=data.content,
                thread_id=conversation.thread_id,
            ):
                chunk_type = chunk.get("type", "")

                if chunk_type == "token":
                    content = chunk.get("content", "")
                    full_response += content
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

                elif chunk_type == "step":
                    yield f"data: {json.dumps({'type': 'step', 'step': chunk.get('step', '')})}\n\n"

                elif chunk_type == "tool_start":
                    tool_name = chunk.get("tool", "")
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name})}\n\n"

                elif chunk_type == "tool_end":
                    tool_name = chunk.get("tool", "")
                    result = chunk.get("result", "")
                    tool_calls_list.append({"name": tool_name, "result": result})
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_name, 'result': result})}\n\n"

                elif chunk_type == "error":
                    yield f"data: {json.dumps({'type': 'error', 'error': chunk.get('error', 'Unknown error')})}\n\n"
                    return

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Save agent message
            if full_response:
                from app.database.session import AsyncSessionLocal
                async with AsyncSessionLocal() as save_session:
                    agent_msg = await AgentChatService.save_agent_message(
                        save_session,
                        conversation_id,
                        full_response,
                        duration_ms=duration_ms,
                        tool_calls=tool_calls_list if tool_calls_list else None,
                    )

                    yield f"data: {json.dumps({'type': 'agent_message', 'message_id': agent_msg.id})}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'thread_id': conversation.thread_id})}\n\n"

        except Exception as e:
            logger.error(f"SSE stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# =============================================================================
# FILE UPLOADS
# =============================================================================

@router.post(
    "/conversations/{conversation_id}/upload",
    response_model=FileUploadResponse,
    summary="Upload a file to a conversation"
)
async def upload_file(
    conversation_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload an image, PDF, or document to a conversation."""
    try:
        # Verify access
        await AgentChatService.get_conversation(db, conversation_id, current_user.id)

        # Read content
        content = await file.read()

        chat_file = await AgentChatService.upload_file(
            db, conversation_id, current_user.id,
            file.filename or "unnamed",
            content,
            file.content_type or "application/octet-stream",
        )

        return FileUploadResponse(
            id=chat_file.id,
            file_name=chat_file.file_name,
            original_file_name=chat_file.original_file_name,
            file_type=chat_file.file_type,
            file_size=chat_file.file_size,
            file_url=f"/api/v1/agent-chat/files/{chat_file.id}",
        )

    except AgentChatServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/files/{file_id}",
    summary="Serve an uploaded file"
)
async def serve_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Serve an uploaded chat file."""
    try:
        chat_file = await AgentChatService.get_file(db, file_id, current_user.id)

        # Build absolute path
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        absolute_path = os.path.join(backend_dir, chat_file.file_path)

        if not os.path.exists(absolute_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        return FileResponse(
            absolute_path,
            filename=chat_file.original_file_name,
            media_type=chat_file.file_type,
        )

    except AgentChatServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))
