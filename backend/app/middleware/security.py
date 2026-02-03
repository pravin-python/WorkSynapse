"""
Security Middleware - Headers, Rate Limiting, Request Validation
"""
from typing import Callable
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.logging import security_logger

# In-memory rate limiting (use Redis in production)
rate_limit_store: dict = defaultdict(list)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security Headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' wss: ws:;"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using config values."""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests_per_minute = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.window_size = 60  # seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        rate_limit_store[client_ip] = [
            timestamp for timestamp in rate_limit_store[client_ip]
            if current_time - timestamp < self.window_size
        ]
        
        # Check rate limit
        if len(rate_limit_store[client_ip]) >= self.requests_per_minute:
            security_logger.log_rate_limit(
                user_id="unknown",
                ip_address=client_ip,
                endpoint=str(request.url.path)
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again later."}
            )
        
        # Record request
        rate_limit_store[client_ip].append(current_time)
        
        # Add rate limit headers
        response = await call_next(request)
        remaining = self.requests_per_minute - len(rate_limit_store[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_size))
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate request size and content type."""
    
    MAX_CONTENT_LENGTH = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request body too large"}
            )
        
        return await call_next(request)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID for tracing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = hashlib.md5(
            f"{time.time()}{request.client.host if request.client else ''}".encode()
        ).hexdigest()[:16]
        
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


def setup_security_middleware(app: FastAPI):
    """Configure all security middleware."""
    
    # Import anti-replay middleware
    from app.middleware.antireplay import AntiReplayMiddleware
    
    # CORS - using origins from config
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS if settings.BACKEND_CORS_ORIGINS else ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=[
            "*",
            "X-API-KEY",
            "X-TIMESTAMP",
            "X-NONCE",
            "X-SIGNATURE"
        ],
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-Nonce-Used",
            "X-RateLimit-Remaining-IP",
            "X-RateLimit-Remaining-Key"
        ]
    )
    
    # Security Headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Anti-Replay Protection (one-time request validation)
    if settings.ANTIREPLAY_ENABLED:
        app.add_middleware(AntiReplayMiddleware)
        security_logger.log_suspicious_activity(
            user_id=None,
            ip_address="system",
            details="Anti-replay middleware enabled"
        )
    
    # Rate Limiting
    app.add_middleware(RateLimitMiddleware)
    
    # Request Validation
    app.add_middleware(RequestValidationMiddleware)
    
    # Request ID Tracing
    app.add_middleware(RequestIDMiddleware)

