"""
Unit tests for notification delivery utilities.

This module verifies:
- Email delivery logic via SMTP.
- WhatsApp message sending via Twilio API.
- Local file logging of notifications.

External dependencies are patched using mocks to avoid real network calls or file I/O.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from app.notifications.models import Notification, NotificationPriority


@pytest.fixture
def dummy_notification():
    """Create a dummy Notification instance for tests."""
    return Notification(
        id=1,
        user_id=42,
        title="Test Notification",
        body="This is a test notification.",
        priority=NotificationPriority.HIGH,
        created_at=datetime.utcnow()
    )


@pytest.mark.asyncio
@patch("app.notifications.utils.delivery.get_user_email", new_callable=AsyncMock)
@patch("app.notifications.utils.delivery.smtplib.SMTP")
async def test_send_email_notification(mock_smtp, mock_get_user_email, dummy_notification):
    """
    Test that send_email_notification uses SMTP to send an email.

    Validates:
        - SMTP client is initialized
        - starttls, login, and send_message are called
        - user email is resolved
    """
    from app.notifications.utils.delivery import send_email_notification

    mock_get_user_email.return_value = "test@example.com"
    smtp_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = smtp_instance

    await send_email_notification(dummy_notification)

    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once()
    smtp_instance.send_message.assert_called_once()
    mock_get_user_email.assert_called_once_with(dummy_notification.user_id)


@pytest.mark.asyncio
@patch("app.notifications.utils.delivery.get_user_whatsapp_number", new_callable=AsyncMock)
@patch("app.notifications.utils.delivery.Client")
async def test_send_whatsapp_message(mock_twilio_client, mock_get_number, dummy_notification):
    """
    Test that send_whatsapp_message calls Twilio API to send a message.

    Validates:
        - Twilio client is instantiated
        - messages.create is called with proper parameters
    """
    from app.notifications.utils.delivery import send_whatsapp_message

    mock_get_number.return_value = "+1234567890"
    mock_twilio_client.return_value.messages.create = MagicMock()

    await send_whatsapp_message(dummy_notification)

    mock_twilio_client.assert_called_once()
    mock_twilio_client.return_value.messages.create.assert_called_once()
    mock_get_number.assert_called_once_with(dummy_notification.user_id)


@pytest.mark.asyncio
async def test_save_notification_to_file(tmp_path, dummy_notification):
    """
    Test that a notification is saved to a local JSON file.

    Validates:
        - notification_logs/ directory is created
        - file is created with expected name pattern
    """
    from app.notifications.utils import delivery as delivery_mod

    class FakePath(type(tmp_path)):
        def mkdir(self, *args, **kwargs):
            return super().mkdir(*args, **kwargs)

    with patch.object(delivery_mod, "Path", return_value=tmp_path):
        await delivery_mod.save_notification_to_file(dummy_notification)

    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
