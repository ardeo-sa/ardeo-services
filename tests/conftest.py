"""
Global test configuration and infrastructure fixtures.

Responsibilities:
- Register shared fixture modules (`tests/fixtures/`)
- Configure async + sync test clients
- Manage event loop lifecycle
"""
import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database.services import get_services_db

pytest_plugins = [
    "tests.fixtures.db",
    "tests.fixtures.users",
    "tests.fixtures.meetings",
    "tests.fixtures.notifications",
]


@pytest.fixture(scope="session")
def event_loop():
    """
    Use a single event loop for the entire test session.
    """
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

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


def load_trigger_conditions_fixture():
    """
    Returns a list of trigger conditions for tests.
    Each item represents a WatchedItem configuration.
    """
    return [
        {
            "user_id": 8,
            "item_type": "meeting",
            "item_id": 1,
            "trigger_conditions": {
                "conditions": [
                    {
                        "field": "scheduled_at",
                        "operator": "within_hours",
                        "value": 3
                    }
                ],
                "logic": "AND"
            }
        }
    ]