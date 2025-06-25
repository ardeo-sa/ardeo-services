# app/tasks/dispatch_notifications.py

from datetime import datetime, timezone
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import async_session_maker
from app.notifications.models import Notification
from app.notifications.utils.delivery import (
    send_email_notification,
    send_whatsapp_message,
    save_notification_to_file,
)


async def dispatch_unsent_notifications():
    """
    Dispatch all queued (unsent) notifications using configured delivery methods.
    Includes retry fallback for email and WhatsApp.
    """
    async with async_session_maker() as session:  # type: AsyncSession
        stmt = select(Notification).where(Notification.sent_at.is_(None))
        result = await session.execute(stmt)
        notifications = result.scalars().all()

        for notif in notifications:
            try:
                await save_notification_to_file(notif)

                # Retry logic (naive exponential backoff on retry count)
                for attempt in range(3):
                    try:
                        await send_email_notification(notif)
                        break
                    except Exception:
                        await asyncio.sleep(2 ** attempt)

                for attempt in range(3):
                    try:
                        await send_whatsapp_message(notif)
                        break
                    except Exception:
                        await asyncio.sleep(2 ** attempt)

                notif.sent_at = datetime.now(timezone.utc)
                await session.commit()

            except Exception:
                # Leave unsent so it gets retried later
                continue


async def start_dispatch_loop(interval_seconds: int = 30):
    """
    Start an infinite dispatch loop to send notifications every X seconds.

    Args:
        interval_seconds (int): Delay between dispatch runs.
    """
    while True:
        await dispatch_unsent_notifications()
        await asyncio.sleep(interval_seconds)
