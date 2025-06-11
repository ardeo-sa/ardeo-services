"""
Database setup and initialization for the services database using SQLAlchemy.
"""
# pylint: disable=invalid-name
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.config import SERVICES_DB_URI

Base = declarative_base()


def get_services_engine():
    """
    Creates and returns a SQLAlchemy engine for connecting to the services database.

    Raises:
        ValueError: If the SERVICES_DB_URI is not defined.

    Returns:
        sqlalchemy.engine.Engine: SQLAlchemy engine instance connected to the services database.
    """
    if not SERVICES_DB_URI:
        raise ValueError("The SERVICES_DB_URI environment variable is not set or is empty.")
    return create_engine(SERVICES_DB_URI, echo=True)


services_engine = None
ServicesSessionLocal = None

def init_services_db():
    """
    Initializes the services database connection by creating the engine and session factory.

    This function sets the global `services_engine` and `ServicesSessionLocal` variables.
    Should be called before performing any database operations.

    Raises:
        ValueError: If the SERVICES_DB_URI is not defined or the engine could not be initialized.
    """
    global services_engine, ServicesSessionLocal  # pylint: disable=global-statement
    if not services_engine:
        services_engine = get_services_engine()
        ServicesSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=services_engine)


def get_services_db() -> Session:
    """
    Provides a database session to be used in FastAPI route functions.

    This will be used as a dependency to inject the session into FastAPI routes.

    Yields:
        Session: A database session instance.
    """
    db = ServicesSessionLocal()
    try:
        yield db
    finally:
        db.close()
