"""
Database setup and initialization for the services database using SQLAlchemy.
"""
# pylint: disable=invalid-name
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.config import get_services_db_uri

Base = declarative_base()

_services_engine = None
_ServicesSessionLocal = None

def get_services_engine() -> "sqlalchemy.engine.Engine":
    """
       Creates and returns a SQLAlchemy engine for connecting to the services database.

       This function uses `get_services_db_uri` to retrieve the database URI,
       ensuring the URI is validated and dynamically fetched from environment variables.

       Raises:
           ValueError: If the SERVICES_DB_URI environment variable is not set or empty.

       Returns:
           sqlalchemy.engine.Engine: SQLAlchemy engine instance connected to the services database.
       """
    services_db_uri = get_services_db_uri()
    return create_engine(services_db_uri, echo=True)


def get_services_engine_cached():
    """
        Lazily initializes and returns the cached SQLAlchemy engine.

        Raises:
            ValueError: If the SERVICES_DB_URI environment variable is not set.

        Returns:
            Engine: Cached SQLAlchemy engine instance.
        """
    global _services_engine
    if _services_engine is None:
        _services_engine = get_services_engine()
    return _services_engine

def get_session_factory():
    """
    Lazily initializes and returns the SQLAlchemy session factory.

    Returns:
        sessionmaker: A SQLAlchemy sessionmaker bound to the services engine.
    """
    global _ServicesSessionLocal
    if _ServicesSessionLocal is None:
        _ServicesSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_services_engine_cached()
        )
    return _ServicesSessionLocal


def get_services_db() -> Session:
    """
    Dependency for FastAPI routes: provides a session to the services database.

    Yields:
        Session: A SQLAlchemy session instance.
    """
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def init_services_db():
    """
    Forces initialization of the services engine and session factory.

    This should be used in production or scripts that need early database setup.
    """
    get_services_engine_cached()
    get_session_factory()

# def init_services_db():
#     """
#     Initializes the services database connection by creating the engine and session factory.
#
#     This function sets the global `services_engine` and `ServicesSessionLocal` variables.
#     Should be called before performing any database operations.
#
#     Raises:
#         ValueError: If the SERVICES_DB_URI is not defined or the engine could not be initialized.
#     """
#     global services_engine, ServicesSessionLocal  # pylint: disable=global-statement
#     if not services_engine:
#         services_engine = get_services_engine()
#         ServicesSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=services_engine)
#
#
# def get_services_db() -> Session:
#     """
#     Provides a database session to be used in FastAPI route functions.
#
#     This will be used as a dependency to inject the session into FastAPI routes.
#
#     Yields:
#         Session: A database session instance.
#     """
#     db = ServicesSessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
