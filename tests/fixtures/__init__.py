"""
Aggregate module for test fixtures.

This package organizes fixtures into logical submodules:
- db.py: Database session + environment variable fixtures
- users.py: User factories and user-related fixtures
- meetings.py: Meeting and participant fixtures
- notifications.py: Notification-related fixtures

Usage:
    from tests.fixtures import db, users, meetings, notifications
"""

from . import db
from . import users
from . import meetings
from . import notifications

__all__ = [
    "db",
    "users",
    "meetings",
    "notifications",
]
