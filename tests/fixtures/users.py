"""
User-related test fixtures.

Includes:
- User factory fixture
- Normal and coordinator users
- FastAPI dependency overrides for get_current_user
"""
# pylint: disable=redefined-outer-name

from uuid import uuid4

import pytest
import pytest_asyncio

from app.main import app
from app.users.models.user import User, UserRole
from app.core.dependencies import get_current_user

from tests.user_factory import UserFactory

@pytest.fixture
def user_factory(sync_db_session): # pylint: disable=redefined-outer-name
    """
    Fixture for user factory.

    Injects the SQLAlchemy session into the factory.
    """
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
        role=UserRole.NORMAL,
        first_name="John",
        last_name="Normal"
    )
    user_factory._meta.sqlalchemy_session.expunge(user)  # pylint: disable=protected-access

    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
    except Exception as e:
        print(f"❌ Commit failed for coordinator_user: {e}")
        raise
    return user


@pytest_asyncio.fixture
async def coordinator_user(db_session, user_factory):
    """
    Create a coordinator user for testing.
    """
    session = db_session
    user = user_factory(
        email=f"coord_{uuid4().hex[:8]}@example.com",
        role=UserRole.COORDINATOR,
        first_name="Jerry",
        last_name="Coordinator"
    )
    user_factory._meta.sqlalchemy_session.expunge(user)  # pylint: disable=protected-access

    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
    except Exception as e:
        print(f"❌ Commit failed for coordinator_user: {e}")
        raise
    return user


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
