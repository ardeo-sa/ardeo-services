"""
Root API router that aggregates and includes all sub-routers from the app.
"""
import logging

from fastapi import APIRouter

from app.calendar.api.router import router as calendar_router

logger = logging.getLogger(__name__)

router = APIRouter()

logger.info("Including calendar router under prefix /api/calendar")
router.include_router(calendar_router, prefix="/api/calendar", tags=["Calendar"])
