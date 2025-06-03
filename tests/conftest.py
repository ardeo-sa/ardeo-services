# tests/conftest.py

"""
Test fixtures for setting up a mock SQLite database and FastAPI test client.

Provides a temporary in-memory SQLite database with tables created from app models.
Overrides FastAPI dependencies to inject test database sessions.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.services import Base  # Your declarative base
from app.main import app
from fastapi.testclient import TestClient
from app.core.dependencies import get_services_db

# Create SQLite in-memory engine and session
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
