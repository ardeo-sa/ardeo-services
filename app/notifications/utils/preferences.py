from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.notifications.models import NotificationPreference


async def get_user_preferences(db: AsyncSession, user_id: int) -> Optional[NotificationPreference]:
    """
    Retrieve a user's notification preferences.

    Args:
        db (AsyncSession): The DB session to use.
        user_id (int): The user ID to look up preferences for.

    Returns:
        NotificationPreference or None
    """
    stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
