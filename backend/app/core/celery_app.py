"""
Celery Worker Configuration and Tasks
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worksynapse",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.worker.tasks.agents",
        "app.worker.tasks.notifications",
        "app.worker.tasks.analytics",
        "app.worker.tasks.download_model",
        "app.worker.tasks.rag"
    ]
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes warning
    worker_prefetch_multiplier=4,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Retry configuration
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Dead letter queue
    task_routes={
        "app.worker.tasks.agents.*": {"queue": "agents"},
        "app.worker.tasks.notifications.*": {"queue": "notifications"},
        "app.worker.tasks.analytics.*": {"queue": "analytics"},
        "app.worker.tasks.download_model.*": {"queue": "downloads"},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "app.worker.tasks.analytics.cleanup_sessions",
            "schedule": 3600.0,  # Every hour
        },
        "generate-daily-analytics": {
            "task": "app.worker.tasks.analytics.generate_daily_report",
            "schedule": 86400.0,  # Every 24 hours
        },
    }
)
