"""
Notification preferences retrieval utilities.

This module provides functions to fetch user notification delivery preferences
from the database. It includes logging for monitoring the retrieval process and errors.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.notifications.models import NotificationPreference

logger = logging.getLogger(__name__)

async def get_user_preferences(db: AsyncSession, user_id: int) -> Optional[NotificationPreference]:
    """
    Retrieve a user's notification preferences.

    Args:
        db (AsyncSession): The DB session to use.
        user_id (int): The user ID to look up preferences for.

    Returns:
        NotificationPreference or None
    """
    try:
        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        result = await db.execute(stmt)
        prefs = result.scalar_one_or_none()
        if prefs:
            logger.info(f"Notification preferences found for user_id={user_id}")
        else:
            logger.info(f"No notification preferences found for user_id={user_id}")
        return prefs
    except Exception as e:
        logger.error(f"Error retrieving notification preferences for user_id={user_id}: {e}")
        return None
