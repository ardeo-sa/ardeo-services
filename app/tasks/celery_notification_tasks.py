"""
Celery tasks for running background notification jobs.
"""

import asyncio
from app.celery_app import celery_app
from app.database.session import async_session_maker
from app.tasks.system_notifications import generate_system_notifications


@celery_app.task
def run_system_notifications():
    """
    Celery task to generate predefined system notifications.
    """
    async def _run():
        async with async_session_maker() as session:
            await generate_system_notifications(session)

    asyncio.run(_run())
