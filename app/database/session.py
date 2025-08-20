"""
Asynchronous database connection management for the services database.

This module configures and provides access to the services database
using SQLAlchemy's async engine and session system. It creates a single
shared `AsyncEngine` instance and a session factory (`async_session_maker`)
that yields `AsyncSession` objects for use in FastAPI route handlers or
background tasks.

Key features:
- Centralized creation and configuration of the async SQLAlchemy engine.
- Dependency function (`get_services_db`) for injecting an async DB session
  into FastAPI endpoints.
- Automatic session cleanup after each request using context management.

Usage example in FastAPI:

    from fastapi import APIRouter, Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.services.db import get_services_db

    router = APIRouter()

    @router.get("/items/")
    async def list_items(db: AsyncSession = Depends(get_services_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import ASYNC_SERVICES_DB_URI

logger = logging.getLogger(__name__)

# Create async engine
logger.info("[DB] Creating async SQLAlchemy engine for services DB.")
engine = create_async_engine(ASYNC_SERVICES_DB_URI, echo=True)

# Create session factory
async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_services_db() -> AsyncSession:
    """
    Async dependency for FastAPI routes:
    yields an AsyncSession connected to the services DB.
    """
    logger.debug("[DB] Opening async session for services DB.")
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            logger.debug("[DB] Closing async session for services DB.")
