"""
Calendar-specific API router. Used to group and organize routes
related to calendar features like meetings, sync, availability, etc.
"""
from fastapi import APIRouter
from app.calendar.api.meetings import router as meetings_router
from app.calendar.api.calendar_oauth import router as calendar_router
from app.calendar.api.calendar_sync import router as calendar_sync_router

router = APIRouter()

router.include_router(meetings_router, prefix="/meetings")
router.include_router(calendar_router, prefix="/calendar/oauth")
router.include_router(calendar_sync_router, prefix="/calendar")
