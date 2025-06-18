"""
Test fixtures for setting up a mock SQLite database and FastAPI test client.

Provides a temporary in-memory SQLite database with tables created from app models.
Overrides FastAPI dependencies to inject test database sessions.
"""
import asyncio
from uuid import uuid4
import importlib

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
import app.config
from app.database.services import get_services_db, Base
from app.users.models.user import User
from app.calendar.models.meeting import Meeting
from app.core.dependencies import get_current_user

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)
AsyncTestingSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
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
# pylint: disable=redefined-outer-name
def client():
    """
    Synchronous test client for use in non-async test functions.
    """
    return TestClient(app)


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

    importlib.reload(app.config)


@pytest.fixture(scope="session")
def event_loop():
    """
    Use a single event loop for the entire test session.
    """
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
# pylint: disable=redefined-outer-name
async def db_engine():
    """
    Create DB schema once for all tests.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine


@pytest_asyncio.fixture
# pylint: disable=redefined-outer-name
async def db_session():
    """
    Creates a new session for each test.
    """
    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession):
    """
    Returns an HTTPX AsyncClient with test overrides.
    """
    async def override_db():
        yield db_session

    app.dependency_overrides[get_services_db] = override_db

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
# pylint: disable=redefined-outer-name
def user_factory(db_session):
    """
    Returns a factory for generating test users.
    """
    # pylint: disable=protected-access
    UserFactory._meta.sqlalchemy_session = db_session

    def factory(**kwargs):
        return UserFactory(**kwargs)

    return factory


@pytest_asyncio.fixture
# pylint: disable=redefined-outer-name
async def normal_user(db_session, user_factory):
    """
    Create a normal user for testing.
    """
    user = user_factory(
        email=f"user_{uuid4().hex[:8]}@example.com",
        role="user",
        name="Normal John"
    )
    db_session.add(user)
    try:
        await db_session.commit()
    except Exception as e:
        print(f"❌ Commit failed for coordinator_user: {e}")
        raise
    return user


@pytest_asyncio.fixture
# pylint: disable=redefined-outer-name
async def coordinator_user(db_session, user_factory):
    """Create a coordinator user."""
    user = user_factory(
        email=f"coord_{uuid4().hex[:8]}@example.com",
        role="coordinator",
        name="Jerry the Coordinator"
    )
    db_session.add(user)
    try:
        await db_session.commit()
    except Exception as e:
        print(f"❌ Commit failed for coordinator_user: {e}")
        raise
    return user


@pytest_asyncio.fixture
async def mock_meeting(db_session, coordinator_user):
    """Create a sample meeting for testing."""
    meeting = Meeting(
        title="MDT Session",
        type="mdt",
        created_by=coordinator_user.id
    )
    db_session.add(meeting)
    await db_session.commit()
    return meeting


def override_user(user):
    """
    Returns a FastAPI override for get_current_user with the given user.
    """
    def _override():
        return user
    return _override


@pytest_asyncio.fixture
async def override_current_user_normal(normal_user: User):
    """
    Override FastAPI dependency to use a normal user.
    """
    app.dependency_overrides[get_current_user] = override_user(normal_user)
    yield
    app.dependency_overrides[get_current_user] = get_current_user


@pytest_asyncio.fixture
async def override_current_user_coord(coordinator_user: User):
    """
    Override FastAPI user dependency with a coordinator user.
    """
    app.dependency_overrides[get_current_user] = override_user(coordinator_user)
    yield
    app.dependency_overrides[get_current_user] = get_current_user


@pytest.fixture
def override_user_dependency(normal_user: User):
    """
    Override FastAPI dependency for get_current_user in sync tests.
    """
    app.dependency_overrides[get_current_user] = lambda: normal_user
    yield
    app.dependency_overrides.clear()
