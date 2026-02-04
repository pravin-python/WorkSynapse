"""
Microsoft Teams Tools
=====================

Tools for interacting with Microsoft Teams.
"""

import logging
from typing import Any, Dict, List, Optional, Type
import httpx

from app.agents.orchestrator.tools.base import BaseTool, ToolResult
from app.agents.orchestrator.config import get_orchestrator_config

logger = logging.getLogger(__name__)


class TeamsSendWebhookMessageTool(BaseTool):
    """Send a message to Microsoft Teams via webhook."""

    name = "teams_send_message"
    description = "Send a message to a Microsoft Teams channel via webhook"
    category = "teams"
    required_permissions = ["can_send_messages"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Message text to send",
                },
                "title": {
                    "type": "string",
                    "description": "Message title (optional)",
                },
                "webhook_url": {
                    "type": "string",
                    "description": "Teams webhook URL (uses default if not provided)",
                },
            },
            "required": ["text"],
        }

    async def execute(
        self,
        text: str,
        title: Optional[str] = None,
        webhook_url: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            url = webhook_url or config.teams_webhook_url

            if not url:
                return ToolResult(
                    success=False,
                    error="Teams webhook URL not configured",
                )

            # Build adaptive card payload
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": title or "WorkSynapse Notification",
                "sections": [
                    {
                        "activityTitle": title or "WorkSynapse Agent",
                        "text": text,
                    }
                ],
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    timeout=30,
                )
                response.raise_for_status()

            return ToolResult(
                success=True,
                data={"message": "Message sent to Teams successfully"},
            )

        except Exception as e:
            logger.error(f"Teams send message error: {e}")
            return ToolResult(success=False, error=str(e))


class TeamsSendAdaptiveCardTool(BaseTool):
    """Send an adaptive card to Microsoft Teams."""

    name = "teams_send_card"
    description = "Send a rich adaptive card to Microsoft Teams"
    category = "teams"
    required_permissions = ["can_send_messages"]

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Card title",
                },
                "body": {
                    "type": "string",
                    "description": "Card body text",
                },
                "facts": {
                    "type": "array",
                    "description": "List of facts to display (key-value pairs)",
                },
                "webhook_url": {
                    "type": "string",
                    "description": "Teams webhook URL (uses default if not provided)",
                },
            },
            "required": ["title", "body"],
        }

    async def execute(
        self,
        title: str,
        body: str,
        facts: Optional[List[Dict[str, str]]] = None,
        webhook_url: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        try:
            config = get_orchestrator_config()
            url = webhook_url or config.teams_webhook_url

            if not url:
                return ToolResult(
                    success=False,
                    error="Teams webhook URL not configured",
                )

            # Build sections
            sections = [
                {
                    "activityTitle": title,
                    "text": body,
                }
            ]

            # Add facts if provided
            if facts:
                sections[0]["facts"] = [
                    {"name": f.get("name", ""), "value": f.get("value", "")}
                    for f in facts
                ]

            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": title,
                "sections": sections,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    timeout=30,
                )
                response.raise_for_status()

            return ToolResult(
                success=True,
                data={"message": "Adaptive card sent to Teams successfully"},
            )

        except Exception as e:
            logger.error(f"Teams send card error: {e}")
            return ToolResult(success=False, error=str(e))


def get_tools() -> List[Type[BaseTool]]:
    """Return all Teams tool classes."""
    return [
        TeamsSendWebhookMessageTool,
        TeamsSendAdaptiveCardTool,
    ]
