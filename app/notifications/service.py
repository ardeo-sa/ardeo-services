"""
notifications.service

Implements the core business logic for managing and dispatching notifications.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from . import models, schemas


class NotificationService:
    """
    Service class to handle notification creation, sending, and user interactions.

    Attributes:
        db (Session): SQLAlchemy database session.
    """
    def __init__(self, db: Session):
        """
        Initialize NotificationService with a DB session.

        Args:
            db (Session): The SQLAlchemy session to use.
        """
        self.db = db

    def create_notification(self, notif_data: schemas.NotificationCreate) -> models.Notification:
        """
        Create and persist a new notification.

        Args:
            notif_data (NotificationCreate): Notification input schema.

        Returns:
            Notification: Created Notification ORM object.
        """
        db_notif = models.Notification(**notif_data.dict())
        self.db.add(db_notif)
        self.db.commit()
        self.db.refresh(db_notif)
        return db_notif

    def send_notification(self, notif: models.Notification) -> None:
        """
        Sends the notification. For now, just updates the sent_at timestamp.

        Args:
            notif (Notification): The notification to send.
        """
        notif.sent_at = datetime.utcnow()
        self.db.commit()

    def mark_as_read(self, notification_id: int) -> models.Notification:
        """
        Mark a notification as read.

        Args:
            notification_id (int): ID of the notification.

        Returns:
            Notification: Updated Notification object.
        """
        notif = self.db.query(models.Notification).get(notification_id)
        if notif:
            notif.status = models.NotificationStatus.READ
            notif.read_at = datetime.utcnow()
            self.db.commit()
        return notif

    def dismiss(self, notification_id: int) -> models.Notification:
        """
        Dismiss a notification.

        Args:
            notification_id (int): ID of the notification.

        Returns:
            Notification: Updated Notification object.
        """
        notif = self.db.query(models.Notification).get(notification_id)
        if notif:
            notif.status = models.NotificationStatus.DISMISSED
            self.db.commit()
        return notif

    def snooze(self, notification_id: int, snooze_until: datetime) -> models.Notification:
        """
        Snooze a notification. Future delivery logic to be implemented.

        Args:
            notification_id (int): ID of the notification.
            snooze_until (datetime): Time until which the notification is snoozed.

        Returns:
            Notification: Updated Notification object.
        """
        notif = self.db.query(models.Notification).get(notification_id)
        if notif:
            notif.status = models.NotificationStatus.SNOOZED
            # Placeholder: store or schedule the snooze_until timestamp
            self.db.commit()
        return notif
