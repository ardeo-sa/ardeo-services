"""
Celery tasks for running background notification jobs.
"""

import asyncio
import logging

from app.celery_app import celery_app
from app.database.session import async_session_maker
from app.tasks.system_notifications import generate_system_notifications

logger = logging.getLogger(__name__)

@celery_app.task
def run_system_notifications():
    """
    Celery task to generate predefined system notifications.
    """
    logger.info("Starting system notifications task")

    async def _run():
        async with async_session_maker() as session:
            await generate_system_notifications(session)
            logger.info("System notifications generated successfully")

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error(f"Error running system notifications task: {e}", exc_info=True)
        raise
