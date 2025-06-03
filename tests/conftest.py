# tests/conftest.py

"""
Test fixtures for setting up a mock SQLite database and FastAPI test client.

Provides a temporary in-memory SQLite database with tables created from app models.
Overrides FastAPI dependencies to inject test database sessions.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.services import get_services_db, Base
from app.users.models.user import User
from app.calendar.models.meeting import Meeting
from app.core.dependencies import get_current_user

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Create all tables before tests
Base.metadata.create_all(bind=engine)

def override_get_db():
    """
    Dependency override to provide a SQLAlchemy session connected to the test DB.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_services_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    """
    Provides a FastAPI TestClient for API testing.
    """
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def db_session():
    """
    Provides a SQLAlchemy session for tests.
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Creates a new database session for a test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """
    FastAPI test client with DB override.
    """
    def override_db():
        return db_session
    app.dependency_overrides[get_services_db] = override_db
    return TestClient(app)


@pytest.fixture
def normal_user(db_session):
    """Create a normal user for testing."""
    user = User(id=1, email="user@example.com", role="user")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def coordinator_user(db_session):
    """Create a coordinator user."""
    user = User(id=2, email="coord@example.com", role="coordinator")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def mock_meeting(db_session, coordinator_user):
    """Create a sample meeting for testing."""
    meeting = Meeting(
        id=1,
        title="MDT Session",
        type="mdt",
        created_by=coordinator_user.id
    )
    db_session.add(meeting)
    db_session.commit()
    return meeting


@pytest.fixture
def override_current_user_normal(client, normal_user):
    """
    Override FastAPI dependency to use a normal user.
    """
    def _get_user():
        return normal_user
    app.dependency_overrides[get_current_user] = _get_user


@pytest.fixture
def override_current_user_coord(client, coordinator_user):
    """
    Override FastAPI dependency to use a coordinator user.
    """
    def _get_user():
        return coordinator_user
    app.dependency_overrides[get_current_user] = _get_user
