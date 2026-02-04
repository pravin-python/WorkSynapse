"""
Slack Tools
===========

Tools for interacting with Slack.
"""

import logging
from typing import Any, Dict, List, Optional, Type
import httpx

from app.agents.orchestrator.tools.base import BaseTool, ToolResult
from app.agents.orchestrator.config import get_orchestrator_config

logger = logging.getLogger(__name__)


class SlackSendMessageTool(BaseTool):
    """Send a message to a Slack channel."""

    name = "slack_send_message"
    description = "Send a message to a Slack channel"
    category = "slack"
    required_permissions = ["can_send_messages"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Slack channel ID or name (e.g., #general or C1234567890)",
                },
                "text": {
                    "type": "string",
                    "description": "Message text to send",
                },
                "thread_ts": {
                    "type": "string",
                    "description": "Thread timestamp to reply in a thread (optional)",
                },
            },
            "required": ["channel", "text"],
        }

    async def execute(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            if not config.slack_bot_token:
                return ToolResult(
                    success=False,
                    error="Slack bot token not configured",
                )

            headers = {
                "Authorization": f"Bearer {config.slack_bot_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "channel": channel,
                "text": text,
            }
            if thread_ts:
                payload["thread_ts"] = thread_ts

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://slack.com/api/chat.postMessage",
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
                data = response.json()

            if not data.get("ok"):
                return ToolResult(
                    success=False,
                    error=data.get("error", "Unknown Slack error"),
                )

            return ToolResult(
                success=True,
                data={
                    "channel": data.get("channel"),
                    "ts": data.get("ts"),
                    "message": "Message sent successfully",
                },
            )

        except Exception as e:
            logger.error(f"Slack send message error: {e}")
            return ToolResult(success=False, error=str(e))


class SlackListChannelsTool(BaseTool):
    """List available Slack channels."""

    name = "slack_list_channels"
    description = "List available Slack channels"
    category = "slack"
    required_permissions = ["can_access_internet"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of channels to return",
                },
            },
            "required": [],
        }

    async def execute(
        self,
        limit: int = 20,
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            if not config.slack_bot_token:
                return ToolResult(
                    success=False,
                    error="Slack bot token not configured",
                )

            headers = {
                "Authorization": f"Bearer {config.slack_bot_token}",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://slack.com/api/conversations.list",
                    params={"limit": min(limit, 100)},
                    headers=headers,
                    timeout=30,
                )
                data = response.json()

            if not data.get("ok"):
                return ToolResult(
                    success=False,
                    error=data.get("error", "Unknown Slack error"),
                )

            channels = [
                {
                    "id": ch["id"],
                    "name": ch["name"],
                    "is_private": ch.get("is_private", False),
                    "num_members": ch.get("num_members", 0),
                }
                for ch in data.get("channels", [])
            ]

            return ToolResult(success=True, data=channels)

        except Exception as e:
            logger.error(f"Slack list channels error: {e}")
            return ToolResult(success=False, error=str(e))


class SlackGetChannelHistoryTool(BaseTool):
    """Get message history from a Slack channel."""

    name = "slack_get_history"
    description = "Get recent messages from a Slack channel"
    category = "slack"
    required_permissions = ["can_access_internet"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Slack channel ID",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of messages to retrieve",
                },
            },
            "required": ["channel"],
        }

    async def execute(
        self,
        channel: str,
        limit: int = 10,
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            if not config.slack_bot_token:
                return ToolResult(
                    success=False,
                    error="Slack bot token not configured",
                )

            headers = {
                "Authorization": f"Bearer {config.slack_bot_token}",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://slack.com/api/conversations.history",
                    params={"channel": channel, "limit": min(limit, 100)},
                    headers=headers,
                    timeout=30,
                )
                data = response.json()

            if not data.get("ok"):
                return ToolResult(
                    success=False,
                    error=data.get("error", "Unknown Slack error"),
                )

            messages = [
                {
                    "text": msg.get("text", ""),
                    "user": msg.get("user", ""),
                    "ts": msg.get("ts", ""),
                    "type": msg.get("type", ""),
                }
                for msg in data.get("messages", [])
            ]

            return ToolResult(success=True, data=messages)

        except Exception as e:
            logger.error(f"Slack get history error: {e}")
            return ToolResult(success=False, error=str(e))


def get_tools() -> List[Type[BaseTool]]:
    """Return all Slack tool classes."""
    return [
        SlackSendMessageTool,
        SlackListChannelsTool,
        SlackGetChannelHistoryTool,
    ]
