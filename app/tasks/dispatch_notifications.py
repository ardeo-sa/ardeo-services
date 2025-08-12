"""
Celery tasks for running background notification dispatch jobs.

This module handles dispatching unsent notifications via configured delivery
methods such as email, WhatsApp, and saving to files. It includes retry logic
and can run continuously in a loop to process queued notifications.
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import async_session_maker
from app.notifications.models import Notification
from app.notifications.utils.delivery import (
    send_email_notification,
    send_whatsapp_message,
    save_notification_to_file,
)

logger = logging.getLogger(__name__)

async def dispatch_unsent_notifications():
    """
    Dispatch all queued (unsent) notifications using configured delivery methods.
    Includes retry fallback for email and WhatsApp.
    """
    async with async_session_maker() as session:  # type: AsyncSession
        stmt = select(Notification).where(Notification.sent_at.is_(None))
        result = await session.execute(stmt)
        notifications = result.scalars().all()

        if not notifications:
            logger.info("No unsent notifications to dispatch.")
            return

        logger.info(f"Dispatching {len(notifications)} unsent notifications")

        for notif in notifications:
            logger.debug(f"Dispatching notification ID {notif.id} for user {notif.user_id}")
            try:
                await save_notification_to_file(notif)
                logger.debug(f"Saved notification ID {notif.id} to file")

                # Retry logic (naive exponential backoff on retry count)
                for attempt in range(3):
                    try:
                        await send_email_notification(notif)
                        logger.info(f"Email sent for notification ID {notif.id} on attempt {attempt + 1}")
                        break
                    except Exception as e:
                        logger.warning(f"Email send failed for notification ID {notif.id} "
                                       f"on attempt {attempt + 1}: {e}")
                        await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to send email after retries for notification ID {notif.id}")

                for attempt in range(3):
                    try:
                        await send_whatsapp_message(notif)
                        logger.info(f"WhatsApp message sent for notification ID {notif.id} on attempt {attempt + 1}")
                        break
                    except Exception as e:
                        logger.warning(f"WhatsApp send failed for notification ID {notif.id} "
                                       f"on attempt {attempt + 1}: {e}")
                        await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to send WhatsApp message after retries for notification ID {notif.id}")

                notif.sent_at = datetime.now(timezone.utc)
                await session.commit()
                logger.info(f"Notification ID {notif.id} marked as sent")

            except Exception as e:
                logger.error(f"Error dispatching notification ID {notif.id}: {e}", exc_info=True)
                # Leave unsent so it gets retried later
                continue


async def start_dispatch_loop(interval_seconds: int = 30):
    """
    Start an infinite dispatch loop to send notifications every X seconds.

    Args:
        interval_seconds (int): Delay between dispatch runs.
    """
    logger.info(f"Starting dispatch loop with interval {interval_seconds} seconds")
    while True:
        try:
            await dispatch_unsent_notifications()
        except Exception as e:
            logger.error(f"Error in dispatch loop: {e}", exc_info=True)
        await asyncio.sleep(interval_seconds)
