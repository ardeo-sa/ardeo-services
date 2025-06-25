"""
User-related service functions for fetching user contact details.

This module provides utility functions to retrieve user-specific information
from the database, such as email addresses and WhatsApp numbers. These services
are typically used by notification or messaging systems to determine where and
how to contact users.

Functions:
    - get_user_email(user_id, db): Retrieves the user's email address.
    - get_user_whatsapp_number(user_id, db): Retrieves the user's WhatsApp number.

All functions require an asynchronous SQLAlchemy session for database access.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.users.models.user import User


async def get_user_email(user_id: int, db: AsyncSession) -> str | None:
    """
    Fetch the email address of a user by ID.

    Args:
        user_id (int): The ID of the user.
        db (AsyncSession): The database session.

    Returns:
        str | None: The user's email address, or None if not found.
    """
    result = await db.execute(select(User.email).where(User.id == user_id))
    email = result.scalar_one_or_none()
    return email


async def get_user_whatsapp_number(user_id: int, db: AsyncSession) -> str | None:
    """
    Fetch the WhatsApp number of a user by ID.

    Args:
        user_id (int): The ID of the user.
        db (AsyncSession): The database session.

    Returns:
        str | None: The user's WhatsApp number, or None if not found.
    """
    result = await db.execute(select(User.whatsapp_number).where(User.id == user_id))
    number = result.scalar_one_or_none()
    return number
