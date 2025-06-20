"""
Contains the SQLAlchemy ORM models for the Notification system.
Defines notification types, statuses, and the Notification database table.
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship

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
    created_at = Column(DateTime, default=datetime.utcnow)
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
            return datetime.utcnow() >= self.snooze_until
        return True

    def is_critical(self):
        """
        Determines if the notification is critical.
        Placeholder for business logic.

        Returns:
            bool: True if critical, False otherwise.
        """
        return False


class WatchedItem(Base):
    """
        Represents a dynamic item that a user wants to monitor for changes or conditions.

        Attributes:
            id (int): Primary key.
            user_id (int): ID of the user watching the item.
            item_type (str): Type of item being watched (e.g., 'form', 'metric', 'pathway_step').
            item_id (int): Unique identifier of the watched item.
            trigger_conditions (dict): JSON-based conditions that must be met to trigger a notification.
            created_at (datetime): Timestamp when the watch was created.
    """
    __tablename__ = "watched_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_type = Column(String, nullable=False)  # e.g., "form", "metric"
    item_id = Column(Integer, nullable=False)
    trigger_conditions = Column(JSON, nullable=True)  # Flexible condition config
    created_at = Column(DateTime, default=datetime.utcnow)

    # Optional relationship
    user = relationship("User", back_populates="watched_items")
