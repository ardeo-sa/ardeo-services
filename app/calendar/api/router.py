"""
Calendar-specific API router. Used to group and organize routes
related to calendar features like meetings, sync, availability, etc.
"""
import logging
from fastapi import APIRouter

from app.calendar.api.meetings import router as meetings_router
from app.calendar.api.calendar_oauth import router as calendar_router
from app.calendar.api.calendar_sync import router as calendar_sync_router

logger = logging.getLogger(__name__)

router = APIRouter()

logger.info("Including meetings router under prefix /meetings")
router.include_router(meetings_router, prefix="/meetings")

logger.info("Including calendar OAuth router under prefix /calendar/oauth")
router.include_router(calendar_router, prefix="/calendar/oauth")

logger.info("Including calendar sync router under prefix /calendar")
router.include_router(calendar_sync_router, prefix="/calendar")
