"""
API endpoints for managing notifications, including system and user-defined notifications,
delivery preferences, watched item triggers, and background dispatch processing.

This module enables interaction with the notification system through RESTful endpoints,
supporting operations like reading, snoozing, dismissing, and delivering notifications
via multiple channels such as in-app, email, WhatsApp, and local files.
"""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_services_db
from app.notifications.models import Notification
from app.notifications.schemas import (
    NotificationCreate,
    NotificationRead,
    WatchedItemCreate,
    WatchedItemRead,
    NotificationPreferenceCreate,
    NotificationPreferenceRead,
)
from app.notifications.services import NotificationService
from app.notifications.utils.delivery import process_queued_notifications
from app.users.models.user import User
from app.users.services import get_user_email, get_user_whatsapp_number
from app.notifications.utils.delivery import (
    send_email_notification,
    send_whatsapp_message,
    save_notification_to_file
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/", response_model=NotificationRead)
async def create_notification(notif: NotificationCreate, db: AsyncSession = Depends(get_services_db)):
    """
    Create a new notification.

    Args:
        notif (NotificationCreate): Notification creation data.
        db (AsyncSession): Database session.

    Returns:
        NotificationRead: The created notification.
    """
    logger.info("Creating notification for user_id=%s, title='%s'", notif.user_id, notif.title)
    service = NotificationService(db)
    created = await service.create_notification(notif)
    logger.info("Notification created: id=%s, status='ACTIVE'", created.id)
    return created


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_as_read(notification_id: int, db: AsyncSession = Depends(get_services_db)):
    """
    Mark a notification as read.

    Args:
        notification_id (int): Notification ID to mark as read.
        db (AsyncSession): Database session.

    Returns:
        NotificationRead: The updated notification.
    """
    logger.info("Marking notification as read: id=%s", notification_id)
    service = NotificationService(db)
    updated = await service.mark_as_read(notification_id)
    logger.info("Notification marked as read: id=%s, status='READ'", updated.id)
    return updated


@router.post("/{notification_id}/dismiss", response_model=NotificationRead)
async def dismiss_notification(notification_id: int, db: AsyncSession = Depends(get_services_db)):
    """
    Dismiss a notification.

    Args:
        notification_id (int): Notification ID to dismiss.
        db (AsyncSession): Database session.

    Returns:
        NotificationRead: The updated notification.
    """
    logger.info("Dismissing notification: id=%s", notification_id)
    service = NotificationService(db)
    updated = await service.dismiss(notification_id)
    logger.info("Notification dismissed: id=%s, status='DISMISSED'", updated.id)
    return updated


@router.post("/{notification_id}/snooze", response_model=NotificationRead)
async def snooze_notification(notification_id: int, until: datetime, db: AsyncSession = Depends(get_services_db)):
    """
    Snooze a notification until a specific time.

    Args:
        notification_id (int): Notification ID to snooze.
        until (datetime): Time until which the notification is snoozed.
        db (AsyncSession): Database session.

    Returns:
        NotificationRead: The updated notification.
    """
    logger.info("Snoozing notification: id=%s until=%s", notification_id, until.isoformat())
    service = NotificationService(db)
    updated = await service.snooze(notification_id, until)
    logger.info("Notification snoozed: id=%s, snoozed_until=%s", updated.id, until.isoformat())
    return updated


@router.get("/active", response_model=List[NotificationRead])
async def get_active_notifications(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_services_db)):
    """
    Retrieve active notifications for the current user.

    Args:
        current_user (User): Authenticated user.
        db (AsyncSession): Database session.

    Returns:
        List[NotificationRead]: A list of active notifications.
    """
    logger.info("Fetching active notifications for user_id=%s", current_user.id)
    service = NotificationService(db)
    notifications = await service.get_active_notifications(current_user.id)
    logger.info("Retrieved %d active notifications for user_id=%s", len(notifications), current_user.id)
    return notifications


@router.post("/watch", response_model=WatchedItemRead)
async def watch_item(watch_data: WatchedItemCreate, db: AsyncSession = Depends(get_services_db)):
    """
    Register a watched item and trigger rules.

    Args:
        watch_data (WatchedItemCreate): Watched item data and rules.
        db (AsyncSession): Database session.

    Returns:
        WatchedItemRead: Created watched item object.
    """
    logger.info("Registering watched item: item=%s, rules=%s", watch_data.item_id, getattr(watch_data, 'rules', None))
    service = NotificationService(db)
    watched_item = await service.watch_item(watch_data)
    logger.info("Watched item registered: id=%s, item=%s", watched_item.id, watch_data.item_id)
    return watched_item


@router.post("/preferences", response_model=NotificationPreferenceRead)
async def set_notification_preferences(pref: NotificationPreferenceCreate, db: AsyncSession = Depends(get_services_db)):
    """
    Set user notification delivery preferences.

    Args:
        pref (NotificationPreferenceCreate): Delivery preference details.
        db (AsyncSession): Database session.

    Returns:
        NotificationPreferenceRead: Saved delivery preferences.
    """
    logger.info(
        "Setting notification preferences for user_id=%s, channels=%s",
        getattr(pref, "user_id", None),
        getattr(pref, "channels", None)
    )
    service = NotificationService(db)
    preferences = await service.set_preferences(pref)
    logger.info(
        "Notification preferences updated for user_id=%s",
        getattr(pref, "user_id", None)
    )
    return preferences


@router.post("/dispatch")
async def manual_dispatch(db: AsyncSession = Depends(get_services_db)):
    """
    Manually trigger the background notification dispatch process.

    Args:
        db (AsyncSession): Database session.

    Returns:
        dict: Status of dispatch execution.
    """
    logger.info("Manual notification dispatch triggered")
    await process_queued_notifications(db)
    logger.info("Manual notification dispatch completed successfully")
    return {"status": "Dispatched"}


@router.post("/test-delivery/{user_id}")
async def test_delivery(user_id: int, db: AsyncSession = Depends(get_services_db)):
    """
    Test delivery of notifications via email, WhatsApp, and local file.

    Args:
        user_id (int): ID of the user to test delivery to.
        db (AsyncSession): Database session.

    Returns:
        dict: Delivery status.
    """
    logger.info("Initiating test notification delivery for user_id=%s", user_id)

    dummy_notification = Notification(
        id=0,  # Not persisted
        user_id=user_id,
        title="Test Notification",
        body="This is a test delivery via all channels.",
        priority="HIGH"
    )

    logger.debug("Dummy notification created: %s",
                 dummy_notification.dict() if hasattr(dummy_notification, "dict") else dummy_notification)

    try:
        logger.info("Sending test email notification for user_id=%s", user_id)
        await send_email_notification(dummy_notification)
        logger.info("Test email notification sent successfully")

        logger.info("Sending test WhatsApp message for user_id=%s", user_id)
        await send_whatsapp_message(dummy_notification)
        logger.info("Test WhatsApp message sent successfully")

        logger.info("Saving test notification to local file for user_id=%s", user_id)
        await save_notification_to_file(dummy_notification)
        logger.info("Test notification saved to file successfully")

    except Exception as e:
        logger.exception("Test notification delivery failed for user_id=%s: %s", user_id, str(e))
        raise

    logger.info("Test notification delivery completed for user_id=%s", user_id)
    return {"status": "Test notification sent via all channels"}
