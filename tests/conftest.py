"""
Test infrastructure fixtures for the FastAPI application.

Includes:
- Database setup and teardown
- Async and sync test clients
- Event loop management
"""

import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database.services import get_services_db, Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

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


@pytest.fixture
def sync_client():
    """
    Synchronous test client for use in non-async test functions.
    """
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(db_session): # pylint: disable=redefined-outer-name
    """
    Returns an HTTPX AsyncClient with overridden DB session.
    """
    async def override_db():
        yield db_session

    app.dependency_overrides[get_services_db] = override_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
