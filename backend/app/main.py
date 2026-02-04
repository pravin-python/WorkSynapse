"""
WorkSynapse API - Main Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time

from app.core.config import settings, validate_production_settings
from app.core.logging import logger
from app.middleware.security import setup_security_middleware
from app.api.v1.api_router import api_router
from app.services.redis_service import redis_service
from app.services.kafka_service import kafka_service
from app.core.activity_logger import setup_activity_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    logger.info("Starting WorkSynapse API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")
    
    # Log safe settings (no secrets)
    logger.info(f"Configuration: {settings.log_safe_settings()}")
    
    # Validate production settings
    try:
        validate_production_settings()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        if settings.ENVIRONMENT == "production":
            raise
    
    # Connect to Redis
    try:
        await redis_service.connect()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
    
    # Start Kafka producer
    try:
        await kafka_service.start_producer()
        logger.info("Kafka producer started")
    except Exception as e:
        logger.warning(f"Kafka producer failed to start: {e}")
    
    # Setup activity logging
    setup_activity_logging()
    
    logger.info("WorkSynapse API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down WorkSynapse API...")
    
    # Disconnect Redis
    await redis_service.disconnect()
    
    # Stop Kafka
    await kafka_service.stop_producer()
    await kafka_service.stop_all_consumers()
    
    logger.info("WorkSynapse API shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Setup security middleware
setup_security_middleware(app)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and K8s probes."""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "services": {}
    }
    
    # Check Redis
    try:
        if redis_service.redis:
            await redis_service.redis.ping()
            health_status["services"]["redis"] = "connected"
        else:
            health_status["services"]["redis"] = "not_initialized"
    except Exception:
        health_status["services"]["redis"] = "disconnected"
        health_status["status"] = "degraded"
    
    # Check Kafka
    try:
        if kafka_service.producer:
            health_status["services"]["kafka"] = "connected"
        else:
            health_status["services"]["kafka"] = "not_initialized"
    except Exception:
        health_status["services"]["kafka"] = "disconnected"
        health_status["status"] = "degraded"
    
    return health_status


# Metrics endpoint (Prometheus compatible)
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # In production, use prometheus_client library
    return {
        "requests_total": 0,
        "active_connections": 0,
        "cache_hits": 0,
        "cache_misses": 0
    }


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to WorkSynapse API",
        "docs": f"{settings.API_V1_STR}/docs" if settings.DEBUG else "Docs disabled in production",
        "version": "1.0.0"
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)




# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Don't expose error details in production
    detail = str(exc) if settings.DEBUG else "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={"detail": detail}
    )
