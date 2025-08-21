"""
Calendar-specific API router. Used to group and organize routes
related to calendar features like meetings, sync, availability, etc.
"""
import logging
from fastapi import APIRouter

from app.calendar.api.meetings import router as meetings_router
from app.calendar.api.calendar_oauth import router as calendar_router
from app.calendar.api.calendar_sync import router as calendar_sync_router
from app.calendar.api.meeting_template import router as meeting_template_router

logger = logging.getLogger(__name__)
templates_logger = logging.getLogger("calendar.meeting_templates")

router = APIRouter()

logger.info("Including meetings router under prefix /meetings")
router.include_router(meetings_router, prefix="/meetings")

templates_logger.info("Including meeting templates router under prefix /meeting-templates")
router.include_router(meeting_template_router, prefix="/meeting-templates")

logger.info("Including calendar OAuth router under prefix /calendar/oauth")
router.include_router(calendar_router, prefix="/calendar/oauth")

logger.info("Including calendar sync router under prefix /calendar")
router.include_router(calendar_sync_router, prefix="/calendar")
