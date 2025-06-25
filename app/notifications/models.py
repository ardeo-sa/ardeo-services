"""
Contains the SQLAlchemy ORM models for the Notification system.
Defines notification types, statuses, and the Notification database table.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.notifications.enums import NotificationType
from app.notifications.enums import NotificationStatus
from app.database.services import Base
from app.notifications.enums import NotificationPriority


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
    priority = Column(SQLEnum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)
    is_system = Column(Boolean, default=False)  # True if sent by admin/system

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

    user = relationship("User", back_populates="watched_items")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # JSON-encoded structure: {'trigger_rules': [...], 'logic': 'AND' | 'OR'}
    trigger_conditions = Column(JSON, nullable=True)

    # Example: ['in_app', 'email', 'sms']
    delivery_methods = Column(JSON, nullable=False, default=["in_app"])

    # Default priority: can be overridden at rule level
    default_priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.MEDIUM)

    created_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) # pylint: disable=not-callable

    user = relationship("User", back_populates="notification_pref")