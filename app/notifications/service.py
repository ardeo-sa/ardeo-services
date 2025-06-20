"""
Implements the core business logic for managing and dispatching notifications.
"""
from datetime import datetime, timezone
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_, select

from app.notifications.models import NotificationStatus, Notification
from  app.notifications.schemas import NotificationCreate


class NotificationService:
    """
    Service class to handle notification creation, sending, and user interactions.

    Attributes:
        db (Session): SQLAlchemy database session.
    """
    def __init__(self, db: AsyncSession):
        """
        Initialize NotificationService with a DB session.

        Args:
            db (Session): The SQLAlchemy session to use.
        """
        self.db = db

    async def create_notification(self, notif_data: NotificationCreate) -> Notification:
        """
        Create and persist a new notification.

        Args:
            notif_data (NotificationCreate): Notification input schema.

        Returns:
            Notification: Created Notification ORM object.
        """
        db_notif = Notification(**notif_data.model_dump())
        self.db.add(db_notif)
        await self.db.commit()
        await self.db.refresh(db_notif)
        return db_notif

    async def send_notification(self, notif: Notification) -> None:
        """
        Sends the notification. For now, just updates the sent_at timestamp.

        Args:
            notif (Notification): The notification to send.
        """
        notif.sent_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def mark_as_read(self, notification_id: int) -> Notification:
        """
        Mark a notification as read.

        Args:
            notification_id (int): ID of the notification.

        Returns:
            Notification: Updated Notification object.
        """
        notif = await self.db.get(Notification, notification_id)

        if notif is None:
            raise ValueError(f"Notification ID {notification_id} not found")

        notif.status = NotificationStatus.READ
        notif.read_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(notif)
        return notif

    async def dismiss(self, notification_id: int) -> Notification:
        """
        Dismiss a notification.

        Args:
            notification_id (int): ID of the notification.

        Returns:
            Notification: Updated Notification object.
        """
        notif = await self.db.get(Notification, notification_id)

        if notif is None:
            raise ValueError(f"Notification ID {notification_id} not found")

        notif.status = NotificationStatus.DISMISSED
        await self.db.commit()
        await self.db.refresh(notif)
        return notif

    async def snooze(self, notification_id: int, snooze_until: datetime) -> Notification:
        """
        Snooze a notification. Future delivery logic to be implemented.

        Args:
            notification_id (int): ID of the notification.
            snooze_until (datetime): Time until which the notification is snoozed.

        Returns:
            Notification: Updated Notification object.
        """
        notif = await self.db.get(Notification, notification_id)
        if notif is None:
            raise ValueError(f"Notification ID {notification_id} not found")

        notif.status = NotificationStatus.SNOOZED
        notif.snooze_until = snooze_until
        await self.db.commit()
        await self.db.refresh(notif)
        return notif

    async def get_active_notifications(self, user_id: int) -> List[Notification]:
        """
            Retrieve all active notifications for a given user.

            Active notifications are defined as:
            - Notifications with status UNREAD, or
            - Notifications with status SNOOZED where the snooze_until time has passed.

            Results are ordered by creation time in descending order.

            Args:
                user_id (int): The ID of the user for whom to fetch notifications.

            Returns:
                List[Notification]: A list of active Notification objects.
        """
        now = datetime.now(timezone.utc)

        stmt = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                or_(
                    Notification.status == NotificationStatus.UNREAD,
                    and_(
                        Notification.status == NotificationStatus.SNOOZED,
                        Notification.snooze_until <= now,
                    ),
                )
            )
            .order_by(Notification.created_at.desc())
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()
