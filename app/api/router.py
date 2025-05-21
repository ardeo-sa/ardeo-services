"""
Root API router that aggregates and includes all sub-routers from the app.
"""
from fastapi import APIRouter
from app.calendar.api.router import router as calendar_router

router = APIRouter()
router.include_router(calendar_router, prefix="/calendar", tags=["Calendar"])
