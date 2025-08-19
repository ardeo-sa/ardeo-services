"""
Notification-related test fixtures.

Includes:
- Loader for sample trigger conditions from JSON files.
- Dummy notification factory for quick unit tests.
"""

import json
from pathlib import Path
import pytest

from app.notifications.models import Notification, NotificationPriority


def load_trigger_conditions_fixture(filename: str = "trigger_conditions.json") -> list:
    """
    Load sample trigger conditions from a JSON fixture file.

    Args:
        filename (str): The name of the JSON file in the fixtures directory.

    Returns:
        list: A list of watched item trigger definitions, including logic and rules.
    """
    path = Path(__file__).parent / "fixtures" / filename
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def dummy_notification():
    """
    Create a dummy Notification object for testing purposes.

    Returns:
        Notification: A mock notification with preset fields.
    """
    return Notification(
        id=1,
        user_id=123,
        title="Test Title",
        message="Test Body",
        priority=NotificationPriority.MEDIUM,
    )
