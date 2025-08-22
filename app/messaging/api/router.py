"""
Messaging API Router.

This module defines the top-level router for all messaging-related endpoints.
It organizes and mounts sub-routers that handle sending, receiving, and
managing messages, ensuring a clean and modular API structure.

Routes:
    /messaging - Includes all messaging-related API endpoints from
                 `app.messaging.api.messaging`.

Example:
    from fastapi import FastAPI
    from app.messaging.router import router as messaging_router

    app = FastAPI()
    app.include_router(messaging_router, prefix="/api")
"""

import logging
from fastapi import APIRouter
from app.messaging.api.messaging import router as messaging_router

logger = logging.getLogger(__name__)

logger.debug("Initializing Messaging API router.")

router = APIRouter()
router.include_router(messaging_router, prefix="/messaging")

logger.debug("Messaging API router registered with prefix '/messaging'.")
