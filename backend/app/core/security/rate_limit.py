"""
WorkSynapse Rate Limiting Module
================================
Rate limiting utilities for API protection.

Features:
- Rate limit key generation
- Rate limit checking with Redis
- Configurable limits
"""
import hashlib
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def generate_rate_limit_key(identifier: str, action: str) -> str:
    """
    Generate a key for rate limiting.
    
    Args:
        identifier: User identifier (IP, user ID, etc.)
        action: Action being rate limited
        
    Returns:
        Redis key for rate limiting
    """
    return f"rate_limit:{action}:{hashlib.md5(identifier.encode()).hexdigest()}"


class RateLimiter:
    """
    Rate limiter using Redis for tracking request counts.
    
    Usage:
        limiter = RateLimiter(redis_service)
        is_allowed = await limiter.check("user_123", "login", limit=5, window=300)
    """
    
    def __init__(self, redis_service=None):
        """
        Initialize rate limiter.
        
        Args:
            redis_service: Redis service instance (optional, will use default if not provided)
        """
        self.redis = redis_service
    
    async def check(
        self,
        identifier: str,
        action: str,
        limit: int = 100,
        window: int = 60,
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            action: Action being rate limited
            limit: Maximum requests in window
            window: Time window in seconds
            
        Returns:
            bool: True if within limit, False if exceeded
        """
        if self.redis is None:
            # No Redis, allow all requests
            return True
        
        key = generate_rate_limit_key(identifier, action)
        
        try:
            current = await self.redis.get(key)
            
            if current is None:
                # First request, set counter
                await self.redis.setex(key, window, 1)
                return True
            
            current = int(current)
            
            if current >= limit:
                logger.warning(
                    f"Rate limit exceeded: {identifier} - {action}",
                    extra={"identifier": identifier, "action": action, "count": current}
                )
                return False
            
            # Increment counter
            await self.redis.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow request
            return True
    
    async def get_remaining(
        self,
        identifier: str,
        action: str,
        limit: int = 100,
    ) -> int:
        """
        Get remaining requests in current window.
        
        Args:
            identifier: Unique identifier
            action: Action being rate limited
            limit: Maximum requests in window
            
        Returns:
            Number of remaining requests
        """
        if self.redis is None:
            return limit
        
        key = generate_rate_limit_key(identifier, action)
        
        try:
            current = await self.redis.get(key)
            if current is None:
                return limit
            return max(0, limit - int(current))
        except Exception:
            return limit
    
    async def reset(self, identifier: str, action: str) -> None:
        """
        Reset rate limit counter for an identifier.
        
        Args:
            identifier: Unique identifier
            action: Action being rate limited
        """
        if self.redis is None:
            return
        
        key = generate_rate_limit_key(identifier, action)
        
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Rate limit reset failed: {e}")


# =============================================================================
# RATE LIMIT PRESETS
# =============================================================================

class RateLimitPresets:
    """Common rate limit configurations."""
    
    # Authentication endpoints
    LOGIN = {"limit": 5, "window": 300}  # 5 per 5 minutes
    REGISTER = {"limit": 3, "window": 3600}  # 3 per hour
    PASSWORD_RESET = {"limit": 3, "window": 3600}  # 3 per hour
    
    # API endpoints
    API_DEFAULT = {"limit": 100, "window": 60}  # 100 per minute
    API_WRITE = {"limit": 30, "window": 60}  # 30 per minute
    API_EXPENSIVE = {"limit": 10, "window": 60}  # 10 per minute
    
    # File uploads
    FILE_UPLOAD = {"limit": 20, "window": 3600}  # 20 per hour
