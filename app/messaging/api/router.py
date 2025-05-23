"""
Messaging-specific API router. Used to group and organize routes
related to sending, reciving and managing messages
"""
from fastapi import APIRouter
from app.messaging.api.messaging import router as messaging_router

router = APIRouter()
router.include_router(messaging_router, prefix="/messaging")
