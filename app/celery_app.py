# app/celery_app.py
import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

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
        "task": "app.notifications.tasks.celery_tasks.run_system_notifications",
        "schedule": crontab(minute="*/5"),
    }
}

celery_app.config_from_object("app.core.config", namespace="CELERY")

# Autodiscover tasks in subdirectories
celery_app.autodiscover_tasks(["app.notifications.tasks"])
