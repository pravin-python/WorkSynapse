"""
WorkSynapse Agent Chat Schemas
===============================
Pydantic schemas for agent chat conversations, messages, and file uploads.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class SenderType(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class ChatMessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    PDF = "pdf"


# =============================================================================
# FILE SCHEMAS
# =============================================================================

class ChatFileResponse(BaseModel):
    """Response schema for a chat file."""
    id: int
    message_id: Optional[int] = None
    conversation_id: int
    file_name: str
    original_file_name: str
    file_path: str
    file_type: str
    file_size: int
    thumbnail_path: Optional[str] = None
    is_rag_ingested: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """Response after uploading a file."""
    id: int
    file_name: str
    original_file_name: str
    file_type: str
    file_size: int
    file_url: str


# =============================================================================
# MESSAGE SCHEMAS
# =============================================================================

class MessageCreate(BaseModel):
    """Schema for sending a new message."""
    content: str = Field(..., min_length=1, max_length=50000)
    message_type: ChatMessageType = ChatMessageType.TEXT
    file_ids: Optional[List[int]] = None


class MessageResponse(BaseModel):
    """Response schema for a single message."""
    id: int
    conversation_id: int
    sender_type: SenderType
    content: str
    message_type: ChatMessageType
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    duration_ms: int = 0
    tool_calls: Optional[List[Dict[str, Any]]] = None
    files: List[ChatFileResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Paginated list of messages."""
    messages: List[MessageResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# =============================================================================
# CONVERSATION SCHEMAS
# =============================================================================

class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    title: Optional[str] = Field(None, max_length=255)


class ConversationResponse(BaseModel):
    """Response schema for a conversation."""
    id: int
    agent_id: int
    user_id: int
    title: Optional[str] = None
    thread_id: str
    is_archived: bool = False
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    total_tokens_used: int = 0
    created_at: datetime
    updated_at: datetime
    # Preview of last message
    last_message_preview: Optional[str] = None

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Paginated list of conversations."""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ConversationDetailResponse(ConversationResponse):
    """Detailed conversation with agent info."""
    agent_name: Optional[str] = None
    agent_avatar_url: Optional[str] = None
    agent_color: Optional[str] = None
