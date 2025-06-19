"""
Defines enums for notification type and status.
"""

from enum import Enum

class NotificationType(str, Enum):
    """Type of notification delivery channel."""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"

class NotificationStatus(str, Enum):
    """Status of the notification."""
    UNREAD = "unread"
    READ = "read"
    SNOOZED = "snoozed"
    DISMISSED = "dismissed"
