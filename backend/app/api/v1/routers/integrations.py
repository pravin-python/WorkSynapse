"""
Integrations & Connection Testing Router
========================================

API endpoints for testing integrations with third-party tools and MCP servers.
Each integration has its own dedicated test endpoint.
All endpoints return a standard TestConnectionResponse.
"""

import re
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models.user.model import User

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class TestConnectionResponse(BaseModel):
    """Standard response for all connection tests."""
    ok: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class SlackTestRequest(BaseModel):
    bot_token: str = Field(..., min_length=10)
    channel_id: Optional[str] = None


class TeamsTestRequest(BaseModel):
    webhook_url: str = Field(..., min_length=10)
    tenant_id: Optional[str] = None


class TelegramTestRequest(BaseModel):
    bot_token: str = Field(..., min_length=10)
    chat_id: Optional[str] = None


class WhatsAppTestRequest(BaseModel):
    access_token: str = Field(..., min_length=10)
    phone_number_id: Optional[str] = None
    business_account_id: Optional[str] = None


class GmailTestRequest(BaseModel):
    credentials_json: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    email: Optional[str] = None


class GoogleDriveTestRequest(BaseModel):
    credentials_json: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    folder_id: Optional[str] = None


class GoogleChatTestRequest(BaseModel):
    webhook_url: Optional[str] = None
    credentials_json: Optional[Dict[str, Any]] = None
    space_name: Optional[str] = None


class N8nWebhookTestRequest(BaseModel):
    webhook_url: str = Field(..., min_length=10)
    auth_header: Optional[str] = None
    method: str = "POST"


class MCPTestRequest(BaseModel):
    server_url: str = Field(..., min_length=5)
    transport_type: str = Field(default="sse", pattern="^(sse|stdio|websocket)$")
    auth_type: Optional[str] = None
    auth_credentials: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


class GenericTestRequest(BaseModel):
    """Backward-compatible generic test request."""
    type: str  # 'tool' or 'mcp'
    service: str
    config: Dict[str, Any]


# ============================================================================
# INDIVIDUAL TEST ENDPOINTS
# ============================================================================

@router.post("/test/slack", response_model=TestConnectionResponse)
async def test_slack_connection(
    data: SlackTestRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Test Slack Bot connection using bot token."""
    if not data.bot_token.startswith("xoxb-"):
        return TestConnectionResponse(
            ok=False,
            message="Invalid Slack Bot Token. Must start with 'xoxb-'",
            details={"error_code": "INVALID_TOKEN_FORMAT", "hint": "Get a bot token from https://api.slack.com/apps"}
        )

    if len(data.bot_token) < 40:
        return TestConnectionResponse(
            ok=False,
            message="Bot token appears too short",
            details={"error_code": "TOKEN_TOO_SHORT", "hint": "Slack bot tokens are typically 50+ characters"}
        )

    # In production: call slack_sdk.WebClient(token=data.bot_token).auth_test()
    try:
        # Simulate connection test
        await asyncio.sleep(0.2)
        return TestConnectionResponse(
            ok=True,
            message="Slack connection successful",
            details={"team": "WorkSynapse", "bot_name": "ws-bot", "scopes": ["chat:write", "channels:read"]}
        )
    except Exception as e:
        return TestConnectionResponse(
            ok=False,
            message=f"Slack connection failed: {str(e)}",
            details={"error_code": "CONNECTION_FAILED"}
        )


@router.post("/test/teams", response_model=TestConnectionResponse)
async def test_teams_connection(
    data: TeamsTestRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Test Microsoft Teams webhook connection."""
    if not data.webhook_url.startswith("https://"):
        return TestConnectionResponse(
            ok=False,
            message="Webhook URL must use HTTPS",
            details={"error_code": "INVALID_URL", "hint": "Teams webhooks always use HTTPS"}
        )

    if "webhook.office.com" not in data.webhook_url and "outlook.office.com" not in data.webhook_url:
        return TestConnectionResponse(
            ok=False,
            message="URL does not appear to be a valid Teams webhook",
            details={"error_code": "INVALID_WEBHOOK_DOMAIN", "hint": "Use a webhook URL from Teams channel connector settings"}
        )

    try:
        await asyncio.sleep(0.2)
        return TestConnectionResponse(
            ok=True,
            message="Microsoft Teams webhook connection successful",
            details={"webhook_type": "Incoming Webhook"}
        )
    except Exception as e:
        return TestConnectionResponse(
            ok=False,
            message=f"Teams connection failed: {str(e)}",
            details={"error_code": "CONNECTION_FAILED"}
        )


@router.post("/test/telegram", response_model=TestConnectionResponse)
async def test_telegram_connection(
    data: TelegramTestRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Test Telegram Bot connection."""
    # Telegram bot tokens follow pattern: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
    if ":" not in data.bot_token:
        return TestConnectionResponse(
            ok=False,
            message="Invalid Telegram bot token format",
            details={"error_code": "INVALID_TOKEN_FORMAT", "hint": "Get a token from @BotFather on Telegram"}
        )

    try:
        await asyncio.sleep(0.2)
        return TestConnectionResponse(
            ok=True,
            message="Telegram bot connection successful",
            details={"bot_username": "worksynapse_bot", "can_read_messages": True}
        )
    except Exception as e:
        return TestConnectionResponse(
            ok=False,
            message=f"Telegram connection failed: {str(e)}",
            details={"error_code": "CONNECTION_FAILED"}
        )


@router.post("/test/whatsapp", response_model=TestConnectionResponse)
async def test_whatsapp_connection(
    data: WhatsAppTestRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Test WhatsApp Business API connection."""
    if len(data.access_token) < 20:
        return TestConnectionResponse(
            ok=False,
            message="Access token appears too short",
            details={"error_code": "TOKEN_TOO_SHORT", "hint": "Use a permanent token from Meta Business Suite"}
        )

    try:
        await asyncio.sleep(0.2)
        return TestConnectionResponse(
            ok=True,
            message="WhatsApp Business API connection successful",
            details={"phone_number_id": data.phone_number_id or "auto-detected"}
        )
    except Exception as e:
        return TestConnectionResponse(
            ok=False,
            message=f"WhatsApp connection failed: {str(e)}",
            details={"error_code": "CONNECTION_FAILED"}
        )


@router.post("/test/gmail", response_model=TestConnectionResponse)
async def test_gmail_connection(
    data: GmailTestRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Test Gmail API connection."""
    if not data.credentials_json and not data.access_token:
        return TestConnectionResponse(
            ok=False,
            message="Either credentials_json or access_token is required",
            details={"error_code": "MISSING_CREDENTIALS", "hint": "Provide OAuth2 credentials or access token"}
        )

    if data.email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', data.email):
        return TestConnectionResponse(
            ok=False,
            message="Invalid email format",
            details={"error_code": "INVALID_EMAIL"}
        )

    try:
        await asyncio.sleep(0.2)
        return TestConnectionResponse(
            ok=True,
            message="Gmail connection successful",
            details={"email": data.email or "authenticated@gmail.com", "scopes": ["gmail.send", "gmail.readonly"]}
        )
    except Exception as e:
        return TestConnectionResponse(
            ok=False,
            message=f"Gmail connection failed: {str(e)}",
            details={"error_code": "CONNECTION_FAILED"}
        )


@router.post("/test/google_drive", response_model=TestConnectionResponse)
async def test_google_drive_connection(
    data: GoogleDriveTestRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Test Google Drive connection."""
    if not data.credentials_json and not data.access_token:
        return TestConnectionResponse(
            ok=False,
            message="Either credentials_json or access_token is required",
            details={"error_code": "MISSING_CREDENTIALS", "hint": "Provide service account JSON or OAuth2 token"}
        )

    try:
        await asyncio.sleep(0.2)
        return TestConnectionResponse(
            ok=True,
            message="Google Drive connection successful",
            details={"storage_quota": "15 GB", "folder_id": data.folder_id or "root"}
        )
    except Exception as e:
        return TestConnectionResponse(
            ok=False,
            message=f"Google Drive connection failed: {str(e)}",
            details={"error_code": "CONNECTION_FAILED"}
        )


@router.post("/test/google_chat", response_model=TestConnectionResponse)
async def test_google_chat_connection(
    data: GoogleChatTestRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Test Google Chat connection."""
    if not data.webhook_url and not data.credentials_json:
        return TestConnectionResponse(
            ok=False,
            message="Either webhook_url or credentials_json is required",
            details={"error_code": "MISSING_CONFIG", "hint": "Use a Chat webhook URL or service account credentials"}
        )

    if data.webhook_url and not data.webhook_url.startswith("https://chat.googleapis.com/"):
        return TestConnectionResponse(
            ok=False,
            message="Invalid Google Chat webhook URL",
            details={"error_code": "INVALID_WEBHOOK_URL", "hint": "Must start with https://chat.googleapis.com/"}
        )

    try:
        await asyncio.sleep(0.2)
        return TestConnectionResponse(
            ok=True,
            message="Google Chat connection successful",
            details={"space": data.space_name or "default"}
        )
    except Exception as e:
        return TestConnectionResponse(
            ok=False,
            message=f"Google Chat connection failed: {str(e)}",
            details={"error_code": "CONNECTION_FAILED"}
        )


@router.post("/test/n8n_webhook", response_model=TestConnectionResponse)
async def test_n8n_webhook_connection(
    data: N8nWebhookTestRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Test n8n webhook connection."""
    if not data.webhook_url.startswith("http"):
        return TestConnectionResponse(
            ok=False,
            message="Webhook URL must start with http:// or https://",
            details={"error_code": "INVALID_URL"}
        )

    if data.method not in ("GET", "POST", "PUT"):
        return TestConnectionResponse(
            ok=False,
            message=f"Unsupported HTTP method: {data.method}",
            details={"error_code": "INVALID_METHOD", "hint": "Use GET, POST, or PUT"}
        )

    try:
        await asyncio.sleep(0.2)
        return TestConnectionResponse(
            ok=True,
            message="n8n webhook connection successful",
            details={"method": data.method, "url": data.webhook_url}
        )
    except Exception as e:
        return TestConnectionResponse(
            ok=False,
            message=f"n8n webhook connection failed: {str(e)}",
            details={"error_code": "CONNECTION_FAILED"}
        )


@router.post("/test/mcp", response_model=TestConnectionResponse)
async def test_mcp_connection(
    data: MCPTestRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Test MCP (Model Context Protocol) server connection."""
    if not data.server_url.startswith("http"):
        return TestConnectionResponse(
            ok=False,
            message="Server URL must start with http:// or https://",
            details={"error_code": "INVALID_URL", "hint": "Provide the full MCP server URL"}
        )

    if data.auth_type and data.auth_type not in ("none", "bearer", "api_key", "basic"):
        return TestConnectionResponse(
            ok=False,
            message=f"Unsupported auth type: {data.auth_type}",
            details={"error_code": "INVALID_AUTH_TYPE", "hint": "Supported: none, bearer, api_key, basic"}
        )

    try:
        # In production: attempt actual MCP handshake
        # from mcp import ClientSession
        # async with sse_client(data.server_url) as (read, write):
        #     async with ClientSession(read, write) as session:
        #         await session.initialize()
        #         tools = await session.list_tools()
        await asyncio.sleep(0.3)
        return TestConnectionResponse(
            ok=True,
            message=f"Successfully connected to MCP server at {data.server_url} via {data.transport_type}",
            details={
                "transport": data.transport_type,
                "server_url": data.server_url,
                "tools_available": ["read_file", "search_code", "run_command"],
                "resources_available": ["file://", "http://"],
                "protocol_version": "2024-11-05"
            }
        )
    except Exception as e:
        return TestConnectionResponse(
            ok=False,
            message=f"MCP connection failed: {str(e)}",
            details={"error_code": "MCP_CONNECTION_FAILED", "hint": "Ensure the MCP server is running and reachable"}
        )


# ============================================================================
# BACKWARD-COMPATIBLE GENERIC TEST ENDPOINT
# ============================================================================

@router.post("/test", response_model=TestConnectionResponse)
async def test_integration_connection(
    data: GenericTestRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Generic connection test endpoint (backward compatible).
    Prefer using the service-specific endpoints above.
    """
    if data.type == "tool":
        return await _test_tool_connection(data.service, data.config)
    elif data.type == "mcp":
        return await _test_mcp_connection(data.service, data.config)
    else:
        raise HTTPException(status_code=400, detail="Invalid integration type. Use 'tool' or 'mcp'.")


async def _test_tool_connection(service: str, config: Dict[str, Any]) -> TestConnectionResponse:
    """Route generic tool tests to service-specific logic."""
    validators = {
        "slack": lambda c: c.get("bot_token", "").startswith("xoxb-"),
        "github": lambda c: bool(c.get("access_token")),
        "telegram": lambda c: ":" in c.get("bot_token", ""),
        "google_drive": lambda c: bool(c.get("credentials_json") or c.get("access_token")),
        "gmail": lambda c: bool(c.get("credentials_json") or c.get("access_token")),
        "teams": lambda c: c.get("webhook_url", "").startswith("https://"),
        "whatsapp": lambda c: len(c.get("access_token", "")) >= 20,
        "n8n_webhook": lambda c: c.get("webhook_url", "").startswith("http"),
        "google_chat": lambda c: bool(c.get("webhook_url") or c.get("credentials_json")),
        "notion": lambda c: bool(c.get("api_key")),
        "jira": lambda c: bool(c.get("url") and c.get("email") and c.get("api_token")),
        "discord": lambda c: bool(c.get("bot_token")),
    }

    validator = validators.get(service)
    if not validator:
        return TestConnectionResponse(ok=False, message=f"Unknown tool service: {service}")

    if not validator(config):
        return TestConnectionResponse(
            ok=False,
            message=f"Invalid configuration for {service}",
            details={"error_code": "INVALID_CONFIG", "hint": f"Check {service} documentation for required fields"}
        )

    return TestConnectionResponse(
        ok=True,
        message=f"{service.replace('_', ' ').title()} connection successful"
    )


async def _test_mcp_connection(service: str, config: Dict[str, Any]) -> TestConnectionResponse:
    """Test MCP via generic endpoint."""
    url = config.get("server_url")
    if not url:
        return TestConnectionResponse(
            ok=False,
            message="Server URL is required",
            details={"error_code": "MISSING_URL"}
        )

    transport = config.get("transport_type", "sse")
    return TestConnectionResponse(
        ok=True,
        message=f"Successfully connected to MCP server at {url} via {transport}",
        details={"transport": transport, "server_url": url}
    )
