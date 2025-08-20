"""
Celery tasks for calendar synchronization.

This module defines background tasks for integrating with external calendar
providers (Google Calendar, Microsoft Outlook). Tasks here are responsible
for periodically fetching events from user calendars and syncing them into
the local system.

Key Features:
- `sync_all_user_calendars`: Periodic task that loops through all users with
  connected calendars and syncs their events into the local database.
- Uses the async `calendar_sync` service layer, wrapped for Celery execution.
- Designed to run automatically via Celery Beat, but can also be triggered
  manually if needed.

Usage:
Import these tasks where you need to schedule or trigger calendar sync jobs,
or rely on the beat schedule configured in `celery_app.py` to run them
periodically.
"""

import asyncio
import logging
# from celery import shared_task
from sqlalchemy import select

from app.celery_app import celery_app
from app.database.session import async_session_maker
from app.users.models.user import User
from app.calendar.services.calendar_sync import sync_user_calendar

logger = logging.getLogger(__name__)


@celery_app.task
def sync_all_user_calendars():
    """
    Celery task to synchronize external calendar events (Google, Microsoft)
    for all users with connected calendars.
    """

    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()

            logger.info(f"Starting calendar sync for {len(users)} users")
            total_synced = 0

            for user in users:
                try:
                    synced_titles = await sync_user_calendar(user, db)
                    logger.info(f"✅ {user.email}: {len(synced_titles)} new meetings synced")
                    total_synced += len(synced_titles)
                except Exception as e: # pylint: disable=broad-exception-caught
                    logger.error(f"Failed to sync {user.email}: {e}")

            return total_synced

    synced_count = asyncio.run(_run())
    return {"status": "ok", "meetings_synced": synced_count}
