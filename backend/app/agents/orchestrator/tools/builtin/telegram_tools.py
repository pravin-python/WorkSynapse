"""
Telegram Tools
==============

Tools for interacting with Telegram.
"""

import logging
from typing import Any, Dict, List, Optional, Type
import httpx

from app.agents.orchestrator.tools.base import BaseTool, ToolResult
from app.agents.orchestrator.config import get_orchestrator_config

logger = logging.getLogger(__name__)


class TelegramSendMessageTool(BaseTool):
    """Send a message via Telegram bot."""

    name = "telegram_send_message"
    description = "Send a message to a Telegram chat"
    category = "telegram"
    required_permissions = ["can_send_messages"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {
                    "type": "string",
                    "description": "Telegram chat ID to send message to",
                },
                "text": {
                    "type": "string",
                    "description": "Message text to send",
                },
                "parse_mode": {
                    "type": "string",
                    "description": "Parse mode: HTML, Markdown, or MarkdownV2",
                },
            },
            "required": ["chat_id", "text"],
        }

    async def execute(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            if not config.telegram_bot_token:
                return ToolResult(
                    success=False,
                    error="Telegram bot token not configured",
                )

            url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"

            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30)
                data = response.json()

            if not data.get("ok"):
                return ToolResult(
                    success=False,
                    error=data.get("description", "Unknown Telegram error"),
                )

            return ToolResult(
                success=True,
                data={
                    "message_id": data["result"]["message_id"],
                    "chat_id": data["result"]["chat"]["id"],
                },
            )

        except Exception as e:
            logger.error(f"Telegram send message error: {e}")
            return ToolResult(success=False, error=str(e))


class TelegramGetUpdatesTool(BaseTool):
    """Get recent messages from Telegram."""

    name = "telegram_get_updates"
    description = "Get recent updates/messages from the Telegram bot"
    category = "telegram"
    required_permissions = ["can_access_internet"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of updates to retrieve",
                },
                "offset": {
                    "type": "integer",
                    "description": "Offset for pagination",
                },
            },
            "required": [],
        }

    async def execute(
        self,
        limit: int = 10,
        offset: Optional[int] = None,
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            if not config.telegram_bot_token:
                return ToolResult(
                    success=False,
                    error="Telegram bot token not configured",
                )

            url = f"https://api.telegram.org/bot{config.telegram_bot_token}/getUpdates"

            params = {"limit": min(limit, 100)}
            if offset:
                params["offset"] = offset

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30)
                data = response.json()

            if not data.get("ok"):
                return ToolResult(
                    success=False,
                    error=data.get("description", "Unknown Telegram error"),
                )

            updates = []
            for update in data.get("result", []):
                message = update.get("message", {})
                updates.append({
                    "update_id": update["update_id"],
                    "chat_id": message.get("chat", {}).get("id"),
                    "from_user": message.get("from", {}).get("username"),
                    "text": message.get("text", ""),
                    "date": message.get("date"),
                })

            return ToolResult(success=True, data=updates)

        except Exception as e:
            logger.error(f"Telegram get updates error: {e}")
            return ToolResult(success=False, error=str(e))


class TelegramSendDocumentTool(BaseTool):
    """Send a document via Telegram."""

    name = "telegram_send_document"
    description = "Send a document/file to a Telegram chat"
    category = "telegram"
    required_permissions = ["can_send_messages", "can_access_files"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {
                    "type": "string",
                    "description": "Telegram chat ID",
                },
                "document_url": {
                    "type": "string",
                    "description": "URL of the document to send",
                },
                "caption": {
                    "type": "string",
                    "description": "Document caption",
                },
            },
            "required": ["chat_id", "document_url"],
        }

    async def execute(
        self,
        chat_id: str,
        document_url: str,
        caption: str = "",
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            if not config.telegram_bot_token:
                return ToolResult(
                    success=False,
                    error="Telegram bot token not configured",
                )

            url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendDocument"

            payload = {
                "chat_id": chat_id,
                "document": document_url,
                "caption": caption,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30)
                data = response.json()

            if not data.get("ok"):
                return ToolResult(
                    success=False,
                    error=data.get("description", "Unknown Telegram error"),
                )

            return ToolResult(
                success=True,
                data={
                    "message_id": data["result"]["message_id"],
                    "document": data["result"].get("document", {}),
                },
            )

        except Exception as e:
            logger.error(f"Telegram send document error: {e}")
            return ToolResult(success=False, error=str(e))


def get_tools() -> List[Type[BaseTool]]:
    """Return all Telegram tool classes."""
    return [
        TelegramSendMessageTool,
        TelegramGetUpdatesTool,
        TelegramSendDocumentTool,
    ]
