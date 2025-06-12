"""
Unit tests for the NotificationService in app.notifications.service.
"""
import pytest
from datetime import datetime, timedelta

from app.notifications.service import NotificationService
from app.notifications.schemas import NotificationCreate
from app.notifications.enums import NotificationType, NotificationStatus
from app.notifications import models


@pytest.mark.asyncio
async def test_create_notification(db_session):
    """
    Test creating a basic in-app notification.
    """
    service = NotificationService(db_session)
    notif_data = NotificationCreate(
        user_id=1,
        message="Test notification",
        type=NotificationType.IN_APP,
        patient_id=10,
        pathway_step_id=20,
        task_id=30
    )
    notif = service.create_notification(notif_data)

    assert notif.id is not None
    assert notif.user_id == 1
    assert notif.message == "Test notification"
    assert notif.status == NotificationStatus.UNREAD
    assert notif.type == NotificationType.IN_APP
    assert notif.patient_id == 10
    assert notif.task_id == 30
    assert notif.pathway_step_id == 20


@pytest.mark.asyncio
async def test_send_notification_sets_sent_at(db_session):
    """
    Test sending a notification updates the sent_at timestamp.
    """
    service = NotificationService(db_session)

    notif_data = NotificationCreate(
        user_id=2,
        message="Send me!",
        type=NotificationType.IN_APP
    )
    notif = service.create_notification(notif_data)
    assert notif.sent_at is None

    service.send_notification(notif)
    assert notif.sent_at is not None
    assert isinstance(notif.sent_at, datetime)


@pytest.mark.asyncio
async def test_mark_notification_as_read(db_session):
    """
    Test marking a notification as read updates status and timestamp.
    """
    service = NotificationService(db_session)

    notif = service.create_notification(
        NotificationCreate(user_id=3, message="Unread message")
    )
    assert notif.status == NotificationStatus.UNREAD

    updated = service.mark_as_read(notif.id)
    assert updated.status == NotificationStatus.READ
    assert updated.read_at is not None


@pytest.mark.asyncio
async def test_dismiss_notification(db_session):
    """
    Test dismissing a notification.
    """
    service = NotificationService(db_session)

    notif = service.create_notification(
        NotificationCreate(user_id=4, message="To be dismissed")
    )
    updated = service.dismiss(notif.id)

    assert updated.status == NotificationStatus.DISMISSED


@pytest.mark.asyncio
async def test_snooze_notification(db_session):
    """
    Test snoozing a notification.
    """
    service = NotificationService(db_session)

    notif = service.create_notification(
        NotificationCreate(user_id=5, message="Snooze me")
    )
    snooze_until = datetime.utcnow() + timedelta(hours=1)
    updated = service.snooze(notif.id, snooze_until)

    assert updated.status == NotificationStatus.SNOOZED
    # We could store snooze_until if it's later added to the model.


@pytest.mark.asyncio
async def test_triggers_notify_step_completed(db_session):
    """
    Test pathway step completion trigger creates a notification.
    """
    from app.notifications.triggers import notify_step_completed

    notif = notify_step_completed(db_session, user_id=6, patient_id=101, step_id=55)
    assert notif.user_id == 6
    assert notif.patient_id == 101
    assert notif.pathway_step_id == 55
    assert "completed" in notif.message


@pytest.mark.asyncio
async def test_triggers_notify_task_assigned(db_session):
    """
    Test task assignment trigger creates a notification.
    """
    from app.notifications.triggers import notify_task_assigned

    notif = notify_task_assigned(db_session, user_id=7, task_id=77)
    assert notif.user_id == 7
    assert notif.task_id == 77
    assert "assigned" in notif.message
