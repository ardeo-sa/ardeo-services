"""
Celery application configuration for the Ardeo notifications system.

This module sets up and configures the Celery app used for background task
processing, including periodic tasks such as system notification evaluation.

Key Features:
- Uses Redis as both the broker and result backend.
- Configures JSON serialization for tasks and results.
- Sets UTC as the timezone.
- Registers a periodic task (`run_system_notifications`) to run every 5 minutes.
- Loads additional Celery configuration from `app.core.config`.
- Automatically discovers task modules in `app.tasks`.

Usage:
Import `celery_app` in modules where you need to define or queue Celery tasks.
"""

import os
from celery import Celery
from celery.schedules import crontab

# REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


celery_app = Celery(
    "ardeo_notifications",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "run-every-5-min": {
        "task": "app.tasks.celery_notification_tasks.run_system_notifications",
        "schedule": crontab(minute="*/5"),
    },
    "sync-calendars-every-30-min": {
        "task": "app.tasks.calendar_tasks.sync_all_user_calendars",
        "schedule": crontab(minute="*/30"),
    },
}

celery_app.config_from_object("app.config", namespace="CELERY")

# Autodiscover tasks in root
celery_app.autodiscover_tasks(["app"])
