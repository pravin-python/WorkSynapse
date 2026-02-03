"""
Secure Webhook Handler with Signature Verification
"""
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from typing import Optional
import hmac
import hashlib
import time
import json

from app.core.config import settings
from app.core.logging import logger, security_logger
from app.services.redis_service import redis_service
from app.worker.tasks.agents import run_task_generator_agent

router = APIRouter()


def verify_signature(payload: bytes, signature: str, secret: str, algorithm: str = "sha256") -> bool:
    """Verify webhook signature."""
    if not secret:
        logger.warning("Webhook secret not configured")
        return False
    
    if algorithm == "sha256":
        expected = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
    else:
        expected = "sha1=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha1
        ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


async def check_replay_attack(request_id: str, timestamp: int) -> bool:
    """Check for replay attacks using Redis."""
    # Reject if timestamp is too old (5 minutes)
    if abs(time.time() - timestamp) > 300:
        return False
    
    # Check if request ID was already processed
    key = f"webhook:processed:{request_id}"
    if redis_service.redis and await redis_service.redis.exists(key):
        return False
    
    # Store request ID with TTL
    if redis_service.redis:
        await redis_service.redis.set(key, "1", ex=600)  # 10 min TTL
    
    return True


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None),
    x_github_delivery: Optional[str] = Header(None)
):
    """Handle GitHub webhooks with signature verification."""
    payload = await request.body()
    
    # Verify signature
    if not x_hub_signature_256:
        security_logger.log_suspicious_activity(
            None,
            request.client.host if request.client else "unknown",
            "GitHub webhook missing signature"
        )
        raise HTTPException(status_code=401, detail="Missing signature")
    
    # Use secret from environment
    if not settings.GITHUB_WEBHOOK_SECRET:
        logger.error("GITHUB_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook not configured")
    
    if not verify_signature(payload, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET):
        security_logger.log_suspicious_activity(
            None,
            request.client.host if request.client else "unknown",
            "GitHub webhook invalid signature"
        )
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Check replay
    if x_github_delivery:
        is_valid = await check_replay_attack(x_github_delivery, int(time.time()))
        if not is_valid:
            raise HTTPException(status_code=400, detail="Replay attack detected")
    
    # Parse payload
    data = json.loads(payload)
    event_type = x_github_event
    
    logger.info(f"Received GitHub webhook: {event_type}")
    
    # Handle different events
    if event_type == "push":
        # Could trigger deployment or notify team
        pass
    elif event_type == "pull_request":
        # Could create review tasks
        action = data.get("action")
        if action == "opened":
            pr_title = data.get("pull_request", {}).get("title", "")
            # Trigger task generator
            # run_task_generator_agent.delay(f"Review PR: {pr_title}", project_id=1)
    elif event_type == "issues":
        # Could sync with internal tasks
        pass
    
    return {"status": "received", "event": event_type}


@router.post("/jira")
async def jira_webhook(
    request: Request,
    x_atlassian_webhook_identifier: Optional[str] = Header(None)
):
    """Handle Jira webhooks."""
    payload = await request.body()
    data = json.loads(payload)
    
    # Check for replay
    if x_atlassian_webhook_identifier:
        is_valid = await check_replay_attack(x_atlassian_webhook_identifier, int(time.time()))
        if not is_valid:
            raise HTTPException(status_code=400, detail="Replay attack detected")
    
    webhook_event = data.get("webhookEvent", "")
    logger.info(f"Received Jira webhook: {webhook_event}")
    
    # Handle events
    if "issue_created" in webhook_event:
        issue = data.get("issue", {})
        # Sync issue to internal system
        pass
    elif "issue_updated" in webhook_event:
        issue = data.get("issue", {})
        # Update internal task
        pass
    
    return {"status": "received", "event": webhook_event}


@router.post("/custom/{integration_id}")
async def custom_webhook(
    request: Request,
    integration_id: str,
    x_webhook_signature: Optional[str] = Header(None),
    x_webhook_timestamp: Optional[str] = Header(None),
    x_idempotency_key: Optional[str] = Header(None)
):
    """Generic webhook handler for custom integrations."""
    payload = await request.body()
    
    # Verify required headers
    if not x_webhook_signature or not x_webhook_timestamp:
        raise HTTPException(status_code=401, detail="Missing required headers")
    
    # Verify timestamp freshness
    try:
        timestamp = int(x_webhook_timestamp)
        if abs(time.time() - timestamp) > 300:
            raise HTTPException(status_code=401, detail="Timestamp too old")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp")
    
    # Check idempotency
    if x_idempotency_key:
        is_new = await check_replay_attack(x_idempotency_key, timestamp)
        if not is_new:
            return {"status": "already_processed"}
    
    data = json.loads(payload)
    logger.info(f"Received custom webhook for integration {integration_id}")
    
    return {"status": "received", "integration_id": integration_id}
