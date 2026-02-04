"""
Redis Service - Caching, Rate Limiting, Session Store
"""
import json
from typing import Optional, Any
import redis.asyncio as redis
from app.core.config import settings

class RedisClient:
    """Redis client wrapper for caching and rate limiting."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection pool."""
        self.redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
    
    # ==================== CACHING ====================
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cached value."""
        if not self.redis:
            return None
        value = await self.redis.get(f"cache:{key}")
        if value:
            return json.loads(value)
        return None
    
    async def set_cache(self, key: str, value: Any, expire: int = 3600):
        """Set cached value with TTL."""
        if self.redis:
            await self.redis.set(
                f"cache:{key}",
                json.dumps(value),
                ex=expire
            )
    
    async def delete_cache(self, key: str):
        """Delete cached value."""
        if self.redis:
            await self.redis.delete(f"cache:{key}")
    
    # ==================== RATE LIMITING ====================
    
    async def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> tuple[bool, int]:
        """
        Check if rate limit is exceeded.
        Returns (is_allowed, remaining_requests)
        """
        if not self.redis:
            return True, max_requests
        
        key = f"ratelimit:{identifier}"
        current = await self.redis.get(key)
        
        if current is None:
            await self.redis.set(key, 1, ex=window_seconds)
            return True, max_requests - 1
        
        current_count = int(current)
        if current_count >= max_requests:
            return False, 0
        
        await self.redis.incr(key)
        return True, max_requests - current_count - 1
    
    # ==================== SESSION STORE ====================
    
    async def set_session(self, session_id: str, data: dict, expire: int = 86400):
        """Store session data."""
        if self.redis:
            await self.redis.set(
                f"session:{session_id}",
                json.dumps(data),
                ex=expire
            )
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session data."""
        if not self.redis:
            return None
        data = await self.redis.get(f"session:{session_id}")
        if data:
            return json.loads(data)
        return None
    
    async def delete_session(self, session_id: str):
        """Delete session."""
        if self.redis:
            await self.redis.delete(f"session:{session_id}")
    
    # ==================== DISTRIBUTED LOCKS ====================
    
    async def acquire_lock(self, resource: str, ttl: int = 30) -> bool:
        """Acquire a distributed lock."""
        if not self.redis:
            return True
        return await self.redis.set(
            f"lock:{resource}",
            "1",
            nx=True,
            ex=ttl
        )
    
    async def release_lock(self, resource: str):
        """Release a distributed lock."""
        if self.redis:
            await self.redis.delete(f"lock:{resource}")
    
    # ==================== PRESENCE ====================
    
    async def set_user_online(self, user_id: str, channel_id: str):
        """Mark user as online in a channel."""
        if self.redis:
            await self.redis.sadd(f"presence:{channel_id}", user_id)
            await self.redis.expire(f"presence:{channel_id}", 300)
    
    async def set_user_offline(self, user_id: str, channel_id: str):
        """Mark user as offline in a channel."""
        if self.redis:
            await self.redis.srem(f"presence:{channel_id}", user_id)
    
    async def get_online_users(self, channel_id: str) -> list:
        """Get list of online users in a channel."""
        if not self.redis:
            return []
        return list(await self.redis.smembers(f"presence:{channel_id}"))
    
    # ==================== TOKEN BLACKLIST ====================
    
    async def blacklist_token(self, token_jti: str, expires_in: int):
        """Add token to blacklist (for logout)."""
        if self.redis:
            await self.redis.set(f"blacklist:{token_jti}", "1", ex=expires_in)
    
    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """Check if token is blacklisted."""
        if not self.redis:
            return False
        return await self.redis.exists(f"blacklist:{token_jti}") > 0

# Singleton instance
redis_client = RedisClient()
