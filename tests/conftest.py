"""
Test fixtures for setting up a mock SQLite database and FastAPI test client.

Provides a temporary in-memory SQLite database with tables created from app models.
Overrides FastAPI dependencies to inject test database sessions.
"""
import pytest
import asyncio
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient

from app.main import app
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

# Create all tables before tests
Base.metadata.create_all(bind=engine)

# Async override for get_db
async def override_get_db():
    async with AsyncTestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_services_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """
    Use a single event loop for the entire test session.
    """
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def db_engine():
    """
    Create DB schema once for all tests.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine


@pytest.fixture
async def db_session(db_engine):
    """
    Creates a new session for each test.
    """
    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest.fixture
async def async_client(db_session):
    """
    Returns an HTTPX AsyncClient with test overrides.
    """
    async def override_db():
        yield db_session
    app.dependency_overrides[get_services_db] = override_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def normal_user(db_session):
    """
    Create a normal user for testing.
    """
    user = User(id=1, email="user@example.com", role="user")
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def coordinator_user(db_session):
    """Create a coordinator user."""
    user = User(id=2, email="coord@example.com", role="coordinator")
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def mock_meeting(db_session, coordinator_user):
    """Create a sample meeting for testing."""
    meeting = Meeting(
        id=1,
        title="MDT Session",
        type="mdt",
        created_by=coordinator_user.id
    )
    db_session.add(meeting)
    await db_session.commit()
    return meeting


def override_user(user):
    def _override():
        return user
    return _override


@pytest.fixture
async def override_current_user_normal(normal_user):
    """
    Override FastAPI dependency to use a normal user.
    """
    app.dependency_overrides[get_current_user] = override_user(normal_user)


@pytest.fixture
async def override_current_user_coord(coordinator_user):
    app.dependency_overrides[get_current_user] = override_user(coordinator_user)

