"""
Celery application instance — single entry point for all async tasks.

Usage:
    from app.config.celery_app import celery_app
"""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "subscription_management",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks in the /app/tasks/ directory
celery_app.autodiscover_tasks(["app.tasks"])
