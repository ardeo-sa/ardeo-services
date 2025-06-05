# tests/test_calendar_oauth_with_db.py

"""
Tests for calendar OAuth endpoints using an in-memory SQLite test database.

Mocks external HTTP calls and validates API behavior.
"""

import pytest
from unittest.mock import patch

def test_google_oauth_redirect(client):
    """
    Test redirect to Google OAuth consent screen.
    """
    response = client.get("/api/calendar/oauth/google", allow_redirects=False)
    assert response.status_code in (302, 307)
    assert "accounts.google.com" in response.headers["location"]

def test_microsoft_oauth_redirect(client):
    """
    Test redirect to Microsoft OAuth consent screen.
    """
    response = client.get("/api/calendar/oauth/microsoft", allow_redirects=False)
    assert response.status_code in (302, 307)
    assert "login.microsoftonline.com" in response.headers["location"]

@pytest.mark.asyncio
@patch("app.calendar.api.calendar_oauth.Flow.fetch_token")
@patch("app.calendar.api.calendar_oauth.save_calendar_token")
async def test_google_callback(mock_save_token, mock_fetch_token, async_client, db_session):
    """
    Test Google OAuth callback endpoint with mocked token fetching and token saving.
    """
    mock_fetch_token.return_value = None

    class MockCredentials:
        token = "access-token-123"
        refresh_token = "refresh-token-123"
        expiry = None
        token_uri = "token-uri"
        scopes = ["https://www.googleapis.com/auth/calendar.events"]

    with patch("app.calendar.api.calendar_oauth.Flow.credentials", new_callable=property) as mock_cred:
        mock_cred.return_value = MockCredentials()
        response = await async_client.get("/api/calendar/oauth/google/callback?code=fakecode")
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access-token-123"
        assert "refresh_token" in data
        mock_save_token.assert_called_once()


@pytest.mark.asyncio
@patch("requests.post")
@patch("app.calendar.api.calendar_oauth.save_calendar_token")
async def test_microsoft_callback(mock_save_token, mock_post, async_client, db_session):
    """
    Test Microsoft OAuth callback endpoint with mocked HTTP POST and token saving.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "access_token": "ms-access-token",
        "refresh_token": "ms-refresh-token",
        "expires_in": 3600,
        "scope": "offline_access Calendars.ReadWrite",
        "token_type": "Bearer"
    }

    response = await async_client.get("/api/calendar/oauth/microsoft/callback?code=fakecode")
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "ms-access-token"
    mock_save_token.assert_called_once()
