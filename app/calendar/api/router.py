"""
Calendar-specific API router. Used to group and organize routes
related to calendar features like meetings, sync, availability, etc.
"""
from fastapi import APIRouter
from app.calendar.api.meetings import router as meetings_router

router = APIRouter()
router.include_router(meetings_router, prefix="/meetings")
