"""
WorkSynapse Configuration Module
================================
Secure, environment-based configuration following Twelve-Factor App methodology.

All sensitive values MUST come from environment variables.
No secrets should ever be hardcoded in source code.
"""
from typing import List, Optional, Any
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import urllib.parse
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Required variables will raise ValidationError if missing.
    Optional variables have sensible defaults for development only.
    """
    
    # ===========================================
    # APPLICATION
    # ===========================================
    PROJECT_NAME: str = "WorkSynapse API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    LOG_LEVEL: str = "INFO"
    
    # ===========================================
    # SECURITY (REQUIRED - No defaults for secrets)
    # ===========================================
    SECRET_KEY: str  # Required - must be set in environment
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Service-to-service authentication
    SERVICE_API_KEY: str  # Required - must be set in environment
    
    # ===========================================
    # DATABASE (Separate components for flexibility)
    # ===========================================
    POSTGRES_USER: str  # Required
    POSTGRES_PASSWORD: str  # Required
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "worksynapse"
    
    # Computed DATABASE_URL - can be overridden directly
    DATABASE_URL: Optional[str] = None
    
    @model_validator(mode='after')
    def assemble_db_url(self) -> 'Settings':
        """Build DATABASE_URL from components if not provided directly."""
        if self.DATABASE_URL is None:
            # URL-encode password to handle special characters
            encoded_password = urllib.parse.quote_plus(self.POSTGRES_PASSWORD)
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{encoded_password}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self
    
    # Sync database URL for Alembic (uses psycopg2)
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Synchronous database URL for migrations."""
        encoded_password = urllib.parse.quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql://{self.POSTGRES_USER}:{encoded_password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # ===========================================
    # REDIS
    # ===========================================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Computed REDIS_URL - can be overridden directly
    REDIS_URL: Optional[str] = None
    
    @model_validator(mode='after')
    def assemble_redis_url(self) -> 'Settings':
        """Build REDIS_URL from components if not provided directly."""
        if self.REDIS_URL is None:
            if self.REDIS_PASSWORD:
                encoded_password = urllib.parse.quote_plus(self.REDIS_PASSWORD)
                self.REDIS_URL = f"redis://:{encoded_password}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            else:
                self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return self
    
    # ===========================================
    # RABBITMQ / CELERY
    # ===========================================
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    
    # Computed CELERY_BROKER_URL - can be overridden directly
    CELERY_BROKER_URL: Optional[str] = None
    
    @model_validator(mode='after')
    def assemble_celery_url(self) -> 'Settings':
        """Build CELERY_BROKER_URL from components if not provided directly."""
        if self.CELERY_BROKER_URL is None:
            encoded_password = urllib.parse.quote_plus(self.RABBITMQ_PASSWORD)
            vhost = urllib.parse.quote_plus(self.RABBITMQ_VHOST) if self.RABBITMQ_VHOST != "/" else ""
            self.CELERY_BROKER_URL = (
                f"amqp://{self.RABBITMQ_USER}:{encoded_password}"
                f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{vhost}"
            )
        return self
    
    # ===========================================
    # KAFKA
    # ===========================================
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SECURITY_PROTOCOL: str = "PLAINTEXT"  # PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL
    KAFKA_SASL_MECHANISM: Optional[str] = None
    KAFKA_SASL_USERNAME: Optional[str] = None
    KAFKA_SASL_PASSWORD: Optional[str] = None
    
    # ===========================================
    # CORS
    # ===========================================
    # Store as string to avoid pydantic-settings auto-parsing as JSON
    BACKEND_CORS_ORIGINS_STR: str = ""
    
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        v = self.BACKEND_CORS_ORIGINS_STR
        if not v:
            return []
        if v.startswith("["):
            # JSON array format
            import json
            return json.loads(v)
        # Comma-separated format
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    
    # ===========================================
    # EXTERNAL SERVICES
    # ===========================================
    # OpenAI (for AI agents)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    
    # Email (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_TLS: bool = True
    
    # ===========================================
    # WEBHOOK SECRETS
    # ===========================================
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    JIRA_WEBHOOK_SECRET: Optional[str] = None
    
    # ===========================================
    # FILE UPLOADS
    # ===========================================
    UPLOAD_DIR: str = "app/media/uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # ===========================================
    # RATE LIMITING
    # ===========================================
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_WEBSOCKET_MESSAGES_PER_MINUTE: int = 30
    
    # ===========================================
    # ANTI-REPLAY SECURITY
    # ===========================================
    # Enable/disable anti-replay middleware (disable for testing)
    ANTIREPLAY_ENABLED: bool = True
    
    # Timestamp tolerance in seconds (requests outside this window are rejected)
    ANTIREPLAY_TIMESTAMP_TOLERANCE: int = 30
    
    # Nonce TTL in seconds (how long nonces are stored in Redis)
    ANTIREPLAY_NONCE_TTL: int = 60
    
    # IP rate limit per minute for anti-replay protected endpoints
    ANTIREPLAY_IP_RATE_LIMIT: int = 100
    
    # API key rate limit per minute
    ANTIREPLAY_API_KEY_RATE_LIMIT: int = 200
    
    # Number of suspicious activities before IP is blocked
    ANTIREPLAY_SUSPICIOUS_THRESHOLD: int = 5
    
    # Duration in seconds to block suspicious IPs
    ANTIREPLAY_BLOCK_DURATION: int = 900  # 15 minutes
    
    # ===========================================
    # PYDANTIC SETTINGS CONFIG
    # ===========================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra env vars
    )
    
    def log_safe_settings(self) -> dict:
        """Return settings safe to log (no secrets)."""
        return {
            "PROJECT_NAME": self.PROJECT_NAME,
            "ENVIRONMENT": self.ENVIRONMENT,
            "DEBUG": self.DEBUG,
            "LOG_LEVEL": self.LOG_LEVEL,
            "API_V1_STR": self.API_V1_STR,
            "POSTGRES_HOST": self.POSTGRES_HOST,
            "POSTGRES_PORT": self.POSTGRES_PORT,
            "POSTGRES_DB": self.POSTGRES_DB,
            "REDIS_HOST": self.REDIS_HOST,
            "REDIS_PORT": self.REDIS_PORT,
            "RABBITMQ_HOST": self.RABBITMQ_HOST,
            "RABBITMQ_PORT": self.RABBITMQ_PORT,
            "KAFKA_BOOTSTRAP_SERVERS": self.KAFKA_BOOTSTRAP_SERVERS,
            "BACKEND_CORS_ORIGINS": self.BACKEND_CORS_ORIGINS,
            "RATE_LIMIT_REQUESTS_PER_MINUTE": self.RATE_LIMIT_REQUESTS_PER_MINUTE,
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    In tests, you can clear the cache with get_settings.cache_clear()
    """
    return Settings()


# Global settings instance
settings = get_settings()


def validate_production_settings():
    """
    Validate that all required settings are properly configured for production.
    Call this on application startup in production.
    """
    errors = []
    
    if settings.ENVIRONMENT == "production":
        if settings.SECRET_KEY == "change-me-in-production":
            errors.append("SECRET_KEY must be changed in production")
        
        if len(settings.SECRET_KEY) < 32:
            errors.append("SECRET_KEY should be at least 32 characters")
        
        if settings.DEBUG:
            errors.append("DEBUG should be False in production")
        
        if not settings.BACKEND_CORS_ORIGINS:
            errors.append("BACKEND_CORS_ORIGINS should be set in production")
        
        if settings.POSTGRES_PASSWORD == "password":
            errors.append("POSTGRES_PASSWORD must be changed in production")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
