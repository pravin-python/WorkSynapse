"""
Secure WebSocket Handler with JWT Auth and Rate Limiting
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import json
import time
import hashlib
from collections import defaultdict

from app.database.session import get_db
from app.core.security import decode_token
from app.services.user import user as user_service
from app.services.redis_service import redis_service
from app.services.kafka_service import publish_chat_message
from app.core.logging import logger, security_logger

router = APIRouter()

# Message rate limiting per user
message_rate_limits: Dict[str, List[float]] = defaultdict(list)
MAX_MESSAGES_PER_MINUTE = 30
MESSAGE_MAX_LENGTH = 4000

class SecureConnectionManager:
    """WebSocket connection manager with security features."""
    
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}  # channel_id -> {user_id: ws}
    
    async def authenticate(self, websocket: WebSocket, token: str, db: AsyncSession) -> Optional[dict]:
        """Authenticate WebSocket connection."""
        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            return None
        
        payload = decode_token(token)
        if not payload or payload.type != "access":
            await websocket.close(code=4001, reason="Invalid token")
            return None
        
        # Check if token is blacklisted
        if await redis_service.is_token_blacklisted(payload.sub):
            await websocket.close(code=4001, reason="Token revoked")
            return None
        
        user = await user_service.get(db, id=int(payload.sub))
        if not user or not user.is_active:
            await websocket.close(code=4001, reason="User not found or inactive")
            return None
        
        return {"user_id": str(user.id), "email": user.email, "role": payload.role}
    
    async def connect(self, websocket: WebSocket, channel_id: str, user_info: dict):
        """Accept and register connection."""
        await websocket.accept()
        
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = {}
        
        self.active_connections[channel_id][user_info["user_id"]] = websocket
        
        # Update presence in Redis
        await redis_service.set_user_online(user_info["user_id"], channel_id)
        
        # Notify others
        await self.broadcast(channel_id, {
            "type": "user_joined",
            "user_id": user_info["user_id"],
            "timestamp": time.time()
        }, exclude_user=user_info["user_id"])
        
        logger.info(f"User {user_info['user_id']} connected to channel {channel_id}")
    
    def disconnect(self, channel_id: str, user_id: str):
        """Remove connection."""
        if channel_id in self.active_connections:
            self.active_connections[channel_id].pop(user_id, None)
            if not self.active_connections[channel_id]:
                del self.active_connections[channel_id]
    
    async def broadcast(self, channel_id: str, message: dict, exclude_user: Optional[str] = None):
        """Broadcast message to all users in channel."""
        if channel_id not in self.active_connections:
            return
        
        message_str = json.dumps(message)
        for user_id, connection in self.active_connections[channel_id].items():
            if user_id != exclude_user:
                try:
                    await connection.send_text(message_str)
                except Exception:
                    pass
    
    async def send_to_user(self, channel_id: str, user_id: str, message: dict):
        """Send message to specific user."""
        if channel_id in self.active_connections:
            ws = self.active_connections[channel_id].get(user_id)
            if ws:
                await ws.send_text(json.dumps(message))
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user is rate limited."""
        current_time = time.time()
        
        # Clean old entries
        message_rate_limits[user_id] = [
            t for t in message_rate_limits[user_id]
            if current_time - t < 60
        ]
        
        if len(message_rate_limits[user_id]) >= MAX_MESSAGES_PER_MINUTE:
            return False
        
        message_rate_limits[user_id].append(current_time)
        return True
    
    def validate_message(self, content: str) -> tuple[bool, str]:
        """Validate message content."""
        if not content or not content.strip():
            return False, "Empty message"
        
        if len(content) > MESSAGE_MAX_LENGTH:
            return False, f"Message too long (max {MESSAGE_MAX_LENGTH} chars)"
        
        # Basic spam detection (repeated characters)
        if self._is_spam(content):
            return False, "Message flagged as spam"
        
        return True, ""
    
    def _is_spam(self, content: str) -> bool:
        """Simple spam detection."""
        # Check for repeated characters
        if len(set(content)) < 3 and len(content) > 10:
            return True
        # Check for repeated words
        words = content.lower().split()
        if len(words) > 5 and len(set(words)) < 3:
            return True
        return False

manager = SecureConnectionManager()

@router.websocket("/ws/{channel_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Secure WebSocket endpoint with authentication."""
    
    # Authenticate
    user_info = await manager.authenticate(websocket, token, db)
    if not user_info:
        return
    
    # Connect
    await manager.connect(websocket, channel_id, user_info)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
                continue
            
            # Rate limiting
            if not manager.check_rate_limit(user_info["user_id"]):
                await websocket.send_text(json.dumps({
                    "error": "Rate limit exceeded. Please slow down."
                }))
                security_logger.log_rate_limit(
                    user_info["user_id"],
                    websocket.client.host if websocket.client else "unknown",
                    f"websocket:{channel_id}"
                )
                continue
            
            # Validate message
            content = message.get("content", "")
            is_valid, error = manager.validate_message(content)
            if not is_valid:
                await websocket.send_text(json.dumps({"error": error}))
                continue
            
            # Create broadcast message
            broadcast_msg = {
                "type": "message",
                "user_id": user_info["user_id"],
                "content": content,
                "timestamp": time.time(),
                "message_id": hashlib.md5(f"{time.time()}{user_info['user_id']}".encode()).hexdigest()[:12]
            }
            
            # Broadcast to channel
            await manager.broadcast(channel_id, broadcast_msg)
            
            # Publish to Kafka for persistence/analytics
            await publish_chat_message(channel_id, user_info["user_id"], content)
            
    except WebSocketDisconnect:
        manager.disconnect(channel_id, user_info["user_id"])
        await redis_service.set_user_offline(user_info["user_id"], channel_id)
        await manager.broadcast(channel_id, {
            "type": "user_left",
            "user_id": user_info["user_id"],
            "timestamp": time.time()
        })
        logger.info(f"User {user_info['user_id']} disconnected from channel {channel_id}")
