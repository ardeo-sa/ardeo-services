"""
API endpoints for managing notifications, including system and user-defined notifications,
delivery preferences, watched item triggers, and background dispatch processing.

This module enables interaction with the notification system through RESTful endpoints,
supporting operations like reading, snoozing, dismissing, and delivering notifications
via multiple channels such as in-app, email, WhatsApp, and local files.
"""

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
    service = NotificationService(db)
    return await service.create_notification(notif)


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
    service = NotificationService(db)
    return await service.mark_as_read(notification_id)


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
    service = NotificationService(db)
    return await service.dismiss(notification_id)


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
    service = NotificationService(db)
    return await service.snooze(notification_id, until)


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
    service = NotificationService(db)
    return await service.get_active_notifications(current_user.id)


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
    service = NotificationService(db)
    return await service.watch_item(watch_data)


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
    service = NotificationService(db)
    return await service.set_preferences(pref)


@router.post("/dispatch")
async def manual_dispatch(db: AsyncSession = Depends(get_services_db)):
    """
    Manually trigger the background notification dispatch process.

    Args:
        db (AsyncSession): Database session.

    Returns:
        dict: Status of dispatch execution.
    """
    await process_queued_notifications(db)
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
    dummy_notification = Notification(
        id=0,  # Not persisted
        user_id=user_id,
        title="Test Notification",
        body="This is a test delivery via all channels.",
        priority="HIGH"
    )

    await send_email_notification(dummy_notification)
    await send_whatsapp_message(dummy_notification)
    await save_notification_to_file(dummy_notification)

    return {"status": "Test notification sent via all channels"}
