"""
Database-related test fixtures.

Includes:
- Sync SQLAlchemy session for factory_boy
- Mocked environment variables for database and OAuth
"""
import importlib
import pytest
from app.database.services import get_session_factory
import app.config as app_config


@pytest.fixture
def sync_db_session():
    """
    Provides a regular (sync) SQLAlchemy session for sync-only tools like factory_boy.
    """
    session_local = get_session_factory()
    session = session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """
    Mock environmental variables for database and OAuth providers.
    """
    # Mock DB URI
    monkeypatch.setenv("SERVICES_DB_URI", "sqlite:///./test.db")

    # Mock Google OAuth
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fake-google-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fake-google-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost/fake-google-redirect")

    # Mock Microsoft OAuth
    monkeypatch.setenv("MICROSOFT_CLIENT_ID", "fake-microsoft-client-id")
    monkeypatch.setenv("MICROSOFT_CLIENT_SECRET", "fake-microsoft-client-secret")
    monkeypatch.setenv("MICROSOFT_REDIRECT_URI", "http://localhost/fake-microsoft-redirect")

    # Reload config to apply changes
    importlib.reload(app_config)
