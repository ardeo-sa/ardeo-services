"""
Contains the SQLAlchemy ORM models for the Notification system.
Defines notification types, statuses, and the Notification database table.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Enum, DateTime, Text

from app.notifications.enums import NotificationType
from app.notifications.enums import NotificationStatus
from app.database.services import Base

class Notification(Base):
    """
    SQLAlchemy model for notifications.

    Attributes:
        id: Primary key.
        user_id: The ID of the user who should receive the notification.
        patient_id: Optional patient related to the notification.
        pathway_step_id: Optional pathway step related to the notification.
        task_id: Optional task related to the notification.
        type: Type of notification (e.g., in-app, email).
        status: Status of the notification (e.g., unread, read).
        message: The content of the notification.
        created_at: Timestamp when the notification was created.
        sent_at: Timestamp when it was sent.
        read_at: Timestamp when it was read.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    patient_id = Column(Integer, index=True, nullable=True)
    pathway_step_id = Column(Integer, nullable=True)
    task_id = Column(Integer, nullable=True)
    type = Column(Enum(NotificationType), default=NotificationType.IN_APP)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.UNREAD)
    message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    snooze_until = Column(DateTime, nullable=True)

    def is_active(self) -> bool:
        """
        Determine if the notification should be shown to the user.
        """
        if self.status in [NotificationStatus.DISMISSED, NotificationStatus.READ]:
            return False
        if self.status == NotificationStatus.SNOOZED and self.snooze_until:
            return datetime.now(timezone.utc) >= self.snooze_until
        return True

    def is_critical(self):
        """
        Determines if the notification is critical.
        Placeholder for business logic.

        Returns:
            bool: True if critical, False otherwise.
        """
        return False
