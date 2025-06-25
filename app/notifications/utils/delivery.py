"""
Notification delivery utilities.

This module provides helper functions to deliver notifications via
various channels including:

- Email (SMTP)
- WhatsApp (Twilio API)
- Local file logging

Functions are intended to be called from the NotificationService layer.
"""

import smtplib
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.users.services import get_user_email, get_user_whatsapp_number
from app.notifications.models import Notification, NotificationStatus
from app.notifications.utils.preferences import get_user_preferences


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
            return

        msg = EmailMessage()
        msg["Subject"] = notification.title
        msg["From"] = "noreply@yourdomain.com"
        msg["To"] = user_email
        msg.set_content(notification.body)

        with smtplib.SMTP("smtp.yourmail.com", 587, timeout=10) as smtp:
            smtp.starttls()
            smtp.login("your_user", "your_password")
            smtp.send_message(msg)

    except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
        # Replace with logging later
        print(f"[Email Error] Failed to send email to user {notification.user_id}: {e}")


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
            return

        client = Client("TWILIO_SID", "TWILIO_AUTH_TOKEN")
        client.messages.create(
            body=f"{notification.title}\n\n{notification.body}",
            from_="whatsapp:+14155238886",  # Twilio Sandbox number
            to=f"whatsapp:{user_number}"
        )

    except TwilioRestException as e:
        # Replace with logging later
        print(f"[WhatsApp Error] Failed to send WhatsApp message to user {notification.user_id}: {e}")


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

        timestamp = datetime.utcnow().isoformat()
        filename = f"{notification.user_id}_{notification.id}_{timestamp}.json"

        data = {
            "title": notification.title,
            "body": notification.body,
            "priority": notification.priority.value,
            "sent_at": timestamp
        }

        (base_path / filename).write_text(str(data), encoding="utf-8")

    except (OSError, IOError) as e:
        # Replace with logging later
        print(f"[File Save Error] Failed to write notification to file: {e}")


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
    pending_notifications = await Notification.filter(status=NotificationStatus.QUEUED).all()

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
            notification.sent_at = datetime.utcnow()
            await notification.save()

        except Exception as e:
            # Replace with proper logging
            print(f"[Dispatch Error] Failed to process notification {notification.id}: {e}")
