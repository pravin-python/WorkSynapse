"""
Anti-Replay Security Middleware
================================
Zepto-style one-time API request protection system.

Features:
- HMAC-SHA256 request signature verification
- Nonce-based one-time validation (Redis-backed)
- Timestamp expiration (±30 seconds drift tolerance)
- Rate limiting with Redis
- IP throttling
- Suspicious activity logging

Security Headers Required:
- X-API-KEY: Client API key for authentication
- X-TIMESTAMP: Unix timestamp (seconds) when request was made
- X-NONCE: UUID v4 unique per request
- X-SIGNATURE: HMAC-SHA256 signature of request
"""
import time
import hmac
import hashlib
import uuid
from typing import Callable, Optional, Set, Tuple
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.logging import security_logger, logger
from app.services.redis_service import redis_service


# ============================================================================
# CONFIGURATION
# ============================================================================

# Get values from settings with fallback to defaults
def get_timestamp_tolerance() -> int:
    """Get timestamp tolerance from settings."""
    return getattr(settings, 'ANTIREPLAY_TIMESTAMP_TOLERANCE', 30)

def get_nonce_ttl() -> int:
    """Get nonce TTL from settings."""
    return getattr(settings, 'ANTIREPLAY_NONCE_TTL', 60)

def get_ip_rate_limit() -> int:
    """Get IP rate limit from settings."""
    return getattr(settings, 'ANTIREPLAY_IP_RATE_LIMIT', 100)

def get_api_key_rate_limit() -> int:
    """Get API key rate limit from settings."""
    return getattr(settings, 'ANTIREPLAY_API_KEY_RATE_LIMIT', 200)

def get_suspicious_threshold() -> int:
    """Get suspicious activity threshold from settings."""
    return getattr(settings, 'ANTIREPLAY_SUSPICIOUS_THRESHOLD', 5)

def get_block_duration() -> int:
    """Get IP block duration from settings."""
    return getattr(settings, 'ANTIREPLAY_BLOCK_DURATION', 900)

# For backwards compatibility, expose as module-level constants
TIMESTAMP_TOLERANCE_SECONDS: int = get_timestamp_tolerance()
NONCE_TTL_SECONDS: int = get_nonce_ttl()
IP_RATE_LIMIT_PER_MINUTE: int = get_ip_rate_limit()
API_KEY_RATE_LIMIT_PER_MINUTE: int = get_api_key_rate_limit()
SUSPICIOUS_THRESHOLD: int = get_suspicious_threshold()
BLOCK_DURATION_SECONDS: int = get_block_duration()

# Redis key prefixes
NONCE_PREFIX: str = "antireplay:nonce:"
IP_THROTTLE_PREFIX: str = "antireplay:ip:"
API_KEY_THROTTLE_PREFIX: str = "antireplay:apikey:"
SUSPICIOUS_IP_PREFIX: str = "antireplay:suspicious:"


# Endpoints exempt from anti-replay protection (public auth endpoints)
EXEMPT_ENDPOINTS: Set[str] = {
    "/health",
    "/metrics",
    "/",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/docs",
    "/api/v1/openapi.json",
    "/api/v1/redoc",
}

# Endpoints exempt from anti-replay but require authentication
AUTH_ONLY_ENDPOINTS: Set[str] = {
    "/api/v1/webhooks/github",
    "/api/v1/webhooks/jira",
}


# ============================================================================
# ERROR RESPONSES
# ============================================================================

class AntiReplayError:
    """Structured error responses for anti-replay failures."""
    
    @staticmethod
    def missing_headers(missing: list) -> JSONResponse:
        """401: Required security headers are missing."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "missing_security_headers",
                "message": f"Required security headers missing: {', '.join(missing)}",
                "code": "SECURITY_401",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def invalid_api_key() -> JSONResponse:
        """401: Invalid or unrecognized API key."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": "invalid_api_key",
                "message": "The provided API key is invalid or not recognized",
                "code": "SECURITY_401_KEY",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def invalid_signature() -> JSONResponse:
        """403: Request signature verification failed."""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "invalid_signature",
                "message": "Request signature verification failed. Request may have been tampered.",
                "code": "SECURITY_403",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def timestamp_expired() -> JSONResponse:
        """408: Request timestamp is outside acceptable window."""
        return JSONResponse(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            content={
                "error": "timestamp_expired",
                "message": f"Request timestamp is outside the acceptable window (±{TIMESTAMP_TOLERANCE_SECONDS} seconds)",
                "code": "SECURITY_408",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def nonce_reused() -> JSONResponse:
        """409: Nonce has already been used (replay attack detected)."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "nonce_already_used",
                "message": "This request has already been processed. Replay attack detected.",
                "code": "SECURITY_409",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def rate_limited(retry_after: int = 60) -> JSONResponse:
        """429: Rate limit exceeded."""
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please slow down.",
                "code": "SECURITY_429",
                "retry_after": retry_after,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        response.headers["Retry-After"] = str(retry_after)
        return response
    
    @staticmethod
    def ip_blocked() -> JSONResponse:
        """403: IP has been temporarily blocked due to suspicious activity."""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "ip_blocked",
                "message": "Your IP has been temporarily blocked due to suspicious activity",
                "code": "SECURITY_403_IP",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# ============================================================================
# NONCE SERVICE (Redis-backed)
# ============================================================================

class NonceService:
    """
    Redis-backed nonce management for preventing replay attacks.
    
    Each nonce is stored with a TTL to ensure:
    1. A nonce can only be used once
    2. Old nonces are automatically cleaned up
    3. Distributed API servers share nonce state
    """
    
    @staticmethod
    async def is_nonce_used(nonce: str) -> bool:
        """Check if a nonce has already been used."""
        if not redis_service.redis:
            # If Redis is unavailable, log warning and allow request
            # In production, you might want to reject instead
            logger.warning("Redis unavailable for nonce check - allowing request")
            return False
        
        key = f"{NONCE_PREFIX}{nonce}"
        return await redis_service.redis.exists(key) > 0
    
    @staticmethod
    async def mark_nonce_used(nonce: str) -> bool:
        """
        Mark a nonce as used.
        Returns True if successfully marked, False if already exists.
        Uses Redis SET NX (set if not exists) for atomic operation.
        """
        if not redis_service.redis:
            logger.warning("Redis unavailable for nonce marking")
            return True
        
        key = f"{NONCE_PREFIX}{nonce}"
        nonce_ttl = get_nonce_ttl()
        # SET NX with TTL - atomic operation
        result = await redis_service.redis.set(
            key,
            "1",
            nx=True,  # Only set if not exists
            ex=nonce_ttl
        )
        return result is not None
    
    @staticmethod
    def validate_nonce_format(nonce: str) -> bool:
        """Validate that nonce is a valid UUID v4 format."""
        try:
            parsed = uuid.UUID(nonce, version=4)
            return str(parsed) == nonce.lower()
        except (ValueError, AttributeError):
            return False


# ============================================================================
# IP THROTTLING SERVICE
# ============================================================================

class IPThrottleService:
    """
    Redis-backed IP rate limiting and throttling.
    
    Tracks:
    - Request count per IP per minute
    - Suspicious activity patterns
    - Temporary IP blocks
    """
    
    @staticmethod
    async def check_ip_rate_limit(ip_address: str) -> Tuple[bool, int]:
        """
        Check if IP has exceeded rate limit.
        Returns (is_allowed, remaining_requests).
        """
        if not redis_service.redis:
            return True, IP_RATE_LIMIT_PER_MINUTE
        
        key = f"{IP_THROTTLE_PREFIX}{ip_address}"
        current = await redis_service.redis.get(key)
        
        if current is None:
            await redis_service.redis.set(key, 1, ex=60)
            return True, IP_RATE_LIMIT_PER_MINUTE - 1
        
        current_count = int(current)
        if current_count >= IP_RATE_LIMIT_PER_MINUTE:
            return False, 0
        
        await redis_service.redis.incr(key)
        return True, IP_RATE_LIMIT_PER_MINUTE - current_count - 1
    
    @staticmethod
    async def is_ip_blocked(ip_address: str) -> bool:
        """Check if IP is temporarily blocked."""
        if not redis_service.redis:
            return False
        
        key = f"{SUSPICIOUS_IP_PREFIX}{ip_address}"
        return await redis_service.redis.exists(key) > 0
    
    @staticmethod
    async def record_suspicious_activity(ip_address: str, reason: str):
        """
        Record suspicious activity from an IP.
        After threshold suspicious activities, block the IP for configured duration.
        """
        if not redis_service.redis:
            return
        
        block_duration = get_block_duration()
        threshold = get_suspicious_threshold()
        
        key = f"{SUSPICIOUS_IP_PREFIX}{ip_address}:count"
        count = await redis_service.redis.incr(key)
        
        # Set expiry on first increment
        if count == 1:
            await redis_service.redis.expire(key, block_duration)
        
        # Log suspicious activity
        security_logger.log_suspicious_activity(
            user_id=None,
            ip_address=ip_address,
            details=f"Anti-replay: {reason}"
        )
        
        # Block IP after threshold suspicious activities
        if count >= threshold:
            block_key = f"{SUSPICIOUS_IP_PREFIX}{ip_address}"
            await redis_service.redis.set(block_key, reason, ex=block_duration)
            logger.warning(f"IP {ip_address} blocked due to repeated suspicious activity: {reason}")


# ============================================================================
# API KEY RATE LIMITING
# ============================================================================

class APIKeyThrottleService:
    """Rate limiting per API key."""
    
    @staticmethod
    async def check_api_key_rate_limit(api_key: str) -> Tuple[bool, int]:
        """
        Check if API key has exceeded rate limit.
        Returns (is_allowed, remaining_requests).
        """
        if not redis_service.redis:
            return True, API_KEY_RATE_LIMIT_PER_MINUTE
        
        # Hash the API key for storage (don't store plain API keys)
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        key = f"{API_KEY_THROTTLE_PREFIX}{key_hash}"
        current = await redis_service.redis.get(key)
        
        if current is None:
            await redis_service.redis.set(key, 1, ex=60)
            return True, API_KEY_RATE_LIMIT_PER_MINUTE - 1
        
        current_count = int(current)
        if current_count >= API_KEY_RATE_LIMIT_PER_MINUTE:
            return False, 0
        
        await redis_service.redis.incr(key)
        return True, API_KEY_RATE_LIMIT_PER_MINUTE - current_count - 1


# ============================================================================
# SIGNATURE VERIFICATION
# ============================================================================

class SignatureService:
    """
    HMAC-SHA256 request signature generation and verification.
    
    Signature is computed as:
    HMAC_SHA256(method + url_path + body + timestamp + nonce, SECRET_KEY)
    """
    
    @staticmethod
    def compute_signature(
        method: str,
        path: str,
        body: str,
        timestamp: str,
        nonce: str,
        secret_key: str
    ) -> str:
        """
        Compute HMAC-SHA256 signature for request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path (e.g., /api/v1/tasks)
            body: Request body as string (empty string for GET)
            timestamp: Unix timestamp as string
            nonce: UUID v4 nonce
            secret_key: Secret key for HMAC
            
        Returns:
            Hex-encoded HMAC-SHA256 signature
        """
        # Construct message to sign
        message = f"{method.upper()}{path}{body}{timestamp}{nonce}"
        
        # Compute HMAC-SHA256
        signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def verify_signature(
        provided_signature: str,
        method: str,
        path: str,
        body: str,
        timestamp: str,
        nonce: str,
        secret_key: str
    ) -> bool:
        """
        Verify the provided signature matches the computed signature.
        Uses constant-time comparison to prevent timing attacks.
        """
        expected_signature = SignatureService.compute_signature(
            method, path, body, timestamp, nonce, secret_key
        )
        
        # Constant-time comparison
        return hmac.compare_digest(provided_signature.lower(), expected_signature.lower())


# ============================================================================
# TIMESTAMP VALIDATION
# ============================================================================

class TimestampService:
    """Timestamp validation for preventing delayed replay attacks."""
    
    @staticmethod
    def validate_timestamp(timestamp_str: str) -> Tuple[bool, str]:
        """
        Validate that timestamp is within acceptable window.
        
        Args:
            timestamp_str: Unix timestamp as string
            
        Returns:
            (is_valid, error_message)
        """
        try:
            timestamp = int(timestamp_str)
        except (ValueError, TypeError):
            return False, "Invalid timestamp format"
        
        current_time = int(time.time())
        drift = abs(current_time - timestamp)
        tolerance = get_timestamp_tolerance()
        
        if drift > tolerance:
            return False, f"Timestamp drift too large: {drift} seconds"
        
        return True, ""


# ============================================================================
# ANTI-REPLAY MIDDLEWARE
# ============================================================================

class AntiReplayMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive anti-replay protection middleware.
    
    Validates every API request (except exempt endpoints) for:
    1. Required security headers present
    2. Valid API key
    3. Timestamp within acceptable window
    4. Nonce not previously used
    5. HMAC signature matches
    
    On successful validation:
    - Marks nonce as used
    - Allows request through
    
    On failure:
    - Returns appropriate error response
    - Logs suspicious activity
    """
    
    def __init__(self, app, exclude_paths: Optional[Set[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or EXEMPT_ENDPOINTS
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through anti-replay validation."""
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip validation for exempt endpoints
        if self._is_exempt(path):
            return await call_next(request)
        
        # Skip validation for WebSocket upgrade requests
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)
        
        # Check if IP is blocked
        if await IPThrottleService.is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return AntiReplayError.ip_blocked()
        
        # Check IP rate limit
        ip_allowed, ip_remaining = await IPThrottleService.check_ip_rate_limit(client_ip)
        if not ip_allowed:
            security_logger.log_rate_limit(
                user_id="unknown",
                ip_address=client_ip,
                endpoint=path
            )
            return AntiReplayError.rate_limited()
        
        # Skip full validation for auth-only endpoints (webhooks with their own verification)
        if path in AUTH_ONLY_ENDPOINTS:
            return await call_next(request)
        
        # ==================== HEADER VALIDATION ====================
        api_key = request.headers.get("X-API-KEY")
        timestamp = request.headers.get("X-TIMESTAMP")
        nonce = request.headers.get("X-NONCE")
        signature = request.headers.get("X-SIGNATURE")
        
        missing_headers = []
        if not api_key:
            missing_headers.append("X-API-KEY")
        if not timestamp:
            missing_headers.append("X-TIMESTAMP")
        if not nonce:
            missing_headers.append("X-NONCE")
        if not signature:
            missing_headers.append("X-SIGNATURE")
        
        if missing_headers:
            await IPThrottleService.record_suspicious_activity(
                client_ip,
                f"Missing security headers: {', '.join(missing_headers)}"
            )
            return AntiReplayError.missing_headers(missing_headers)
        
        # ==================== API KEY VALIDATION ====================
        # Validate API key (compare with configured service API key)
        # In production, you'd validate against a database of API keys
        if api_key != settings.SERVICE_API_KEY:
            await IPThrottleService.record_suspicious_activity(
                client_ip,
                "Invalid API key"
            )
            return AntiReplayError.invalid_api_key()
        
        # Check API key rate limit
        key_allowed, key_remaining = await APIKeyThrottleService.check_api_key_rate_limit(api_key)
        if not key_allowed:
            security_logger.log_rate_limit(
                user_id="api_key",
                ip_address=client_ip,
                endpoint=path
            )
            return AntiReplayError.rate_limited()
        
        # ==================== TIMESTAMP VALIDATION ====================
        is_valid_time, time_error = TimestampService.validate_timestamp(timestamp)
        if not is_valid_time:
            await IPThrottleService.record_suspicious_activity(
                client_ip,
                f"Timestamp validation failed: {time_error}"
            )
            return AntiReplayError.timestamp_expired()
        
        # ==================== NONCE VALIDATION ====================
        # Validate nonce format
        if not NonceService.validate_nonce_format(nonce):
            await IPThrottleService.record_suspicious_activity(
                client_ip,
                "Invalid nonce format"
            )
            return AntiReplayError.nonce_reused()
        
        # Check if nonce was already used
        if await NonceService.is_nonce_used(nonce):
            await IPThrottleService.record_suspicious_activity(
                client_ip,
                f"Nonce reuse detected: {nonce}"
            )
            logger.warning(f"Replay attack detected from {client_ip}: nonce {nonce}")
            return AntiReplayError.nonce_reused()
        
        # ==================== SIGNATURE VERIFICATION ====================
        # Get request body
        body = b""
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
        
        body_str = body.decode('utf-8') if body else ""
        
        # Verify signature
        is_valid_sig = SignatureService.verify_signature(
            provided_signature=signature,
            method=request.method,
            path=path,
            body=body_str,
            timestamp=timestamp,
            nonce=nonce,
            secret_key=settings.SECRET_KEY
        )
        
        if not is_valid_sig:
            await IPThrottleService.record_suspicious_activity(
                client_ip,
                "Signature verification failed"
            )
            logger.warning(f"Invalid signature from {client_ip} for {request.method} {path}")
            return AntiReplayError.invalid_signature()
        
        # ==================== MARK NONCE AS USED ====================
        # Atomically mark nonce as used (handles race conditions)
        if not await NonceService.mark_nonce_used(nonce):
            # Another request with same nonce was processed
            await IPThrottleService.record_suspicious_activity(
                client_ip,
                f"Concurrent nonce reuse: {nonce}"
            )
            return AntiReplayError.nonce_reused()
        
        # ==================== PROCESS REQUEST ====================
        # All validations passed - process the request
        logger.info(
            f"Anti-replay validation passed",
            extra={
                "ip_address": client_ip,
                "path": path,
                "method": request.method,
                "event_type": "ANTIREPLAY_SUCCESS"
            }
        )
        
        # Reconstruct request with body for downstream handlers
        # (since we consumed the body stream)
        if body:
            request._body = body
        
        response = await call_next(request)
        
        # Add security headers to response
        response.headers["X-Nonce-Used"] = nonce
        response.headers["X-RateLimit-Remaining-IP"] = str(ip_remaining)
        response.headers["X-RateLimit-Remaining-Key"] = str(key_remaining)
        
        return response
    
    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from anti-replay validation."""
        # Exact match
        if path in self.exclude_paths:
            return True
        
        # Prefix match for docs/openapi
        exempt_prefixes = ("/api/v1/docs", "/api/v1/openapi.json", "/api/v1/redoc")
        return any(path.startswith(prefix) for prefix in exempt_prefixes)


# ============================================================================
# MIDDLEWARE SETUP
# ============================================================================

def setup_antireplay_middleware(app, enabled: bool = True):
    """
    Setup anti-replay middleware on FastAPI app.
    
    Args:
        app: FastAPI application
        enabled: Whether to enable anti-replay protection (disable for testing)
    """
    if enabled:
        app.add_middleware(AntiReplayMiddleware)
        logger.info("Anti-replay middleware enabled")
    else:
        logger.warning("Anti-replay middleware disabled - NOT FOR PRODUCTION")
