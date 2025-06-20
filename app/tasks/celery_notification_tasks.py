"""
Celery tasks for running background notification jobs.
"""

from app.celery_app import celery_app
from app.database.services.session import async_session_maker
from app.tasks.system_notifications import generate_system_notifications


@celery_app.task
def run_system_notifications():
    """
    Celery task to generate predefined system notifications.
    """
    import asyncio

    async def run():
        async with async_session_maker() as session:
            await generate_system_notifications(session)

    asyncio.run(run())


TODO!!! use appriorpriate db methods