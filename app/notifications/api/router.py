"""
Notifications-specific API router. Used to group and organize routes
related to creating and managing notifications
"""
from fastapi import APIRouter
from app.notifications.api.notifications import router as notifications_router

router = APIRouter()

router.include_router(notifications_router, prefix="/notifications")
