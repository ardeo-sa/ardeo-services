"""
Notification delivery utilities.

This module provides helper functions to deliver notifications via
various channels including:

- Email (SMTP)
- WhatsApp (Twilio API)
- Local file logging

Functions are intended to be called from the NotificationService layer.
"""
import json
import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM,
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
)
from app.users.services import get_user_email, get_user_whatsapp_number
from app.notifications.models import Notification, NotificationStatus
from app.notifications.utils.preferences import get_user_preferences

logger = logging.getLogger(__name__)


async def send_email_notification(notification: Notification):
    """
    Send a notification to the user via email.

    Uses SMTP to send a simple text email to the recipient.

    Args:
        notification (Notification): The notification to send.

    Raises:
        None. Errors are silently ignored for now.
    """
    try:
        user_email = await get_user_email(notification.user_id)
        if not user_email:
            logger.warning("No email found for user_id=%s. Skipping email notification.", notification.user_id)
            return

        title = notification.title or "Notification"
        msg = EmailMessage()
        msg["Subject"] = title
        msg["From"] = SMTP_FROM
        msg["To"] = user_email
        msg.set_content(notification.message)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)

        logger.info("Email notification sent to user_id=%s at %s", notification.user_id, user_email)

    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        logger.error("Failed to send email to user_id=%s: %s", notification.user_id, e, exc_info=True)


async def send_whatsapp_message(notification: Notification):
    """
    Send a notification to the user via WhatsApp using Twilio.

    Args:
        notification (Notification): The notification to send.

    Notes:
        Requires Twilio credentials and sandbox setup.
        Assumes the user's WhatsApp number is accessible.
    """
    try:
        user_number = await get_user_whatsapp_number(notification.user_id)
        if not user_number:
            logger.warning("No WhatsApp number found for user_id=%s. Skipping WhatsApp notification.",
                           notification.user_id)
            return

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=notification.message,
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{user_number}"
        )
        logger.info("WhatsApp notification sent to user_id=%s at %s", notification.user_id, user_number)

    except TwilioRestException as e:
        logger.error("Failed to send WhatsApp message to user_id=%s: %s", notification.user_id, e, exc_info=True)


async def save_notification_to_file(notification: Notification):
    """
    Save a notification as a local `.json` file for offline access or auditing.

    Files are stored in a `notification_logs/` folder and named using:
    `{user_id}_{notification_id}_{timestamp}.json`

    Args:
        notification (Notification): The notification to save.
    """
    try:
        base_path = Path("notification_logs")
        base_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).isoformat()
        filename = f"{notification.user_id}_{notification.id}_{timestamp}.json"

        data = {
            "message": notification.message,
            "priority": notification.priority.value if notification.priority else "UNKNOWN",
            "sent_at": timestamp
        }

        file_path = base_path / filename
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Notification saved to file %s", file_path)

    except (OSError, IOError) as e:
        logger.error("Failed to write notification to file: %s", e, exc_info=True)


async def process_queued_notifications(db: AsyncSession):
    """
    Process all pending notifications that need to be delivered.

    Fetches notifications with status 'QUEUED' or similar,
    determines delivery preferences, and attempts to send via
    each configured channel (email, WhatsApp, local file, etc).

    This function is meant to run periodically in a background task.

    Raises:
        None. Errors are caught and logged internally.
    """

    # Query for queued notifications
    try:
        # Adjusted: assuming async query using SQLAlchemy async ORM methods
        stmt = Notification.__table__.select().where(Notification.status == NotificationStatus.QUEUED)
        result = await db.execute(stmt)
        pending_notifications = result.scalars().all()

        for notification in pending_notifications:
            try:
                prefs = await get_user_preferences(db, notification.user_id)
                delivery_methods = prefs.delivery_methods if prefs else ["in_app"]

                if "email" in delivery_methods:
                    await send_email_notification(notification)

                if "whatsapp" in delivery_methods:
                    await send_whatsapp_message(notification)

                if "file" in delivery_methods:
                    await save_notification_to_file(notification)

                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now(timezone.utc)

                await notification.save()

                logger.info("Processed notification id=%s for user_id=%s", notification.id, notification.user_id)

            except Exception as e:
                logger.error("Failed to process notification id=%s: %s", notification.id, e, exc_info=True)

    except Exception as e:
        logger.error("Failed to fetch queued notifications: %s", e, exc_info=True)
