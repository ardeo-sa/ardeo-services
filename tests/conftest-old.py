"""
Test fixtures for setting up a mock SQLite database and FastAPI test client.

Provides a temporary in-memory SQLite database with tables created from app models.
Overrides FastAPI dependencies to inject test database sessions.
"""
import asyncio
from uuid import uuid4
import importlib
import json
from pathlib import Path

import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient

from user_factory import UserFactory

from app.main import app
import app.config as app_config
from app.database.services import get_services_db, Base, get_session_factory
from app.users.models.user import User, UserRole
from app.calendar.models.meeting import Meeting
from app.core.dependencies import get_current_user
from app.notifications.models import Notification, NotificationPriority


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)
AsyncTestingSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Async override for get_db
async def override_get_db():
    """
        Override FastAPI DB dependency to use the test session.
    """
    async with AsyncTestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_services_db] = override_get_db


@pytest.fixture
def sync_client():
    """
    Synchronous test client for use in non-async test functions.
    """
    return TestClient(app)


@pytest.fixture
def sync_db_session():
    """Provides a regular (sync) SQLAlchemy session for sync-only tools like factory_boy."""
    session_local = get_session_factory()
    session = session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environmental variables"""
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

    importlib.reload(app_config)


@pytest.fixture(scope="session")
def event_loop():
    """
    Use a single event loop for the entire test session.
    """
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_db_schema():
    """
    Create DB schema once for all tests.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine


@pytest_asyncio.fixture
async def db_session():
    """
    Creates a new session for each test.
    """
    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(db_session): # pylint: disable=redefined-outer-name
    """Returns an HTTPX AsyncClient with overridden DB session."""
    async def override_db():
        yield db_session

    app.dependency_overrides[get_services_db] = override_db

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def user_factory(sync_db_session):  # pylint: disable=redefined-outer-name
    """fixture for user factory"""
    # Inject the SQLAlchemy session into the factory
    UserFactory._meta.sqlalchemy_session = sync_db_session # pylint: disable=protected-access
    return UserFactory


@pytest_asyncio.fixture
async def normal_user(db_session, user_factory): # pylint: disable=redefined-outer-name
    """
    Create a normal user for testing.
    """
    session = db_session
    user = user_factory(
        email=f"user_{uuid4().hex[:8]}@example.com",
        role= UserRole.NORMAL,
        first_name="John",
        last_name="Normal"
    )
    user_factory._meta.sqlalchemy_session.expunge(user) # pylint: disable=protected-access

    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
    except Exception as e:
        print(f"❌ Commit failed for coordinator_user: {e}")
        raise
    return user


@pytest_asyncio.fixture
async def coordinator_user(db_session, user_factory): # pylint: disable=redefined-outer-name
    """Create a coordinator user."""
    session = db_session
    user = user_factory(
        email=f"coord_{uuid4().hex[:8]}@example.com",
        role=UserRole.COORDINATOR,
        first_name="Jerry",
        last_name="Coordinator"
    )
    user_factory._meta.sqlalchemy_session.expunge(user) # pylint: disable=protected-access

    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
    except Exception as e:
        print(f"❌ Commit failed for coordinator_user: {e}")
        raise
    return user


@pytest_asyncio.fixture
async def mock_meeting(db_session, coordinator_user): # pylint: disable=redefined-outer-name
    """Create a sample meeting for testing."""
    session = db_session
    coord = coordinator_user
    meeting = Meeting(
        title="MDT Session",
        type="mdt",
        created_by=coord.id
    )
    session.add(meeting)
    await session.commit()
    return meeting


def override_user(user: User):
    """
    Returns a FastAPI override for get_current_user with the given user.
    """
    def _override():
        return user
    return _override


@pytest_asyncio.fixture
async def override_current_user_normal(normal_user): # pylint: disable=redefined-outer-name
    """
    Override FastAPI dependency to use a normal user.
    """
    user = normal_user
    app.dependency_overrides[get_current_user] = override_user(user)
    yield
    app.dependency_overrides[get_current_user] = get_current_user


@pytest_asyncio.fixture
async def override_current_user_coord(coordinator_user): # pylint: disable=redefined-outer-name
    """
    Override FastAPI user dependency with a coordinator user.
    """
    user = coordinator_user
    app.dependency_overrides[get_current_user] = override_user(user)
    yield
    app.dependency_overrides[get_current_user] = get_current_user


@pytest.fixture
def override_user_dependency(normal_user): # pylint: disable=redefined-outer-name
    """
    Override FastAPI dependency for get_current_user in sync tests.
    """
    user = normal_user
    app.dependency_overrides[get_current_user] = lambda: user
    yield
    app.dependency_overrides.clear()


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


