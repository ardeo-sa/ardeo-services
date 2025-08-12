"""
Notifications API router for the Ardeo-services application.

This module groups and mounts all notification-related routes under the `/notifications` prefix.

Responsibilities:
    - Provide a dedicated namespace for notification-related endpoints.
    - Include the sub-router from `app.notifications.api.notifications`.

Imported routers:
    - notifications_router: Contains CRUD operations and management endpoints for user notifications.
"""
from fastapi import APIRouter
from app.notifications.api.notifications import router as notifications_router

router = APIRouter()

# Mount all notification-related endpoints
router.include_router(notifications_router, prefix="/notifications")
