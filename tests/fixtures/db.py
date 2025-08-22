"""
Database-related test fixtures.

Responsibilities:
- Async test DB engine + session factory
- Create/drop schema once per test session
- Provide async + sync DB sessions for tests
- Override FastAPI DB dependency
- Mock environment variables (OAuth)
"""
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database.services import get_services_db, Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
SYNC_DATABASE_URL = TEST_DATABASE_URL.replace("+aiosqlite", "")

# --- Async DB engine + session factory ---
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

# --- Override FastAPI dependency ---
async def override_get_db():
    """
        Override FastAPI DB dependency to use the test session.
    """
    async with AsyncTestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_services_db] = override_get_db


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
async def db_session() -> AsyncSession:
    """
    Creates a new session for each test.
    """
    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest.fixture
def sync_db_session():
    """
        Provide a synchronous SQLAlchemy session for testing.

        This fixture creates a new SQLite in-memory database (or the URL
        defined in SYNC_DATABASE_URL), initializes the schema, and yields
        a session for use in tests. The session is automatically closed
        after the test completes.

        Yields:
            Session: A synchronous SQLAlchemy session bound to the test database.
    """
    sync_engine = create_engine(SYNC_DATABASE_URL, connect_args={"check_same_thread": False})
    session_factory = sessionmaker(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """
    Mock environmental variables for database and OAuth providers.
    """
    # Mock Google OAuth
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "fake-google-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "fake-google-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost/fake-google-redirect")

    # Mock Microsoft OAuth
    monkeypatch.setenv("MICROSOFT_CLIENT_ID", "fake-microsoft-client-id")
    monkeypatch.setenv("MICROSOFT_CLIENT_SECRET", "fake-microsoft-client-secret")
    monkeypatch.setenv("MICROSOFT_REDIRECT_URI", "http://localhost/fake-microsoft-redirect")
