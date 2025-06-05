"""
Service for managing calendar OAuth tokens.

This module provides functionality to persist OAuth tokens for external
calendar providers (e.g., Google Calendar, Microsoft Outlook) on a
per-user basis. It supports saving new tokens or updating existing ones
while normalizing expiry formats and storing raw token metadata for
future use or auditing.
"""
from typing import Literal
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.calendar.models.oauth import CalendarOAuthToken
from app.users.models.user import User

def save_calendar_token(
    db: Session,
    user: User,
    provider: Literal["google", "microsoft"],
    token_data: dict,
):
    """
    Save or update calendar OAuth token for the user and provider.
    Extracts and stores key fields like access_token, refresh_token, expiry, etc.,
    in addition to keeping the full raw token_data as a JSON blob.
    """
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    token_type = token_data.get("token_type")
    scope = token_data.get("scope")
    expiry_raw = token_data.get("expiry") or token_data.get("expires_at")

    expiry = None
    if expiry_raw:
        if isinstance(expiry_raw, str):
            expiry = datetime.fromisoformat(expiry_raw)
        elif isinstance(expiry_raw, (int, float)):
            expiry = datetime.fromtimestamp(expiry_raw, tz=timezone.utc)

    existing = (
        db.query(CalendarOAuthToken)
        .filter_by(user_id=user.id, provider=provider)
        .first()
    )

    if existing:
        existing.access_token = access_token
        existing.refresh_token = refresh_token
        existing.token_type = token_type
        existing.scope = scope
        existing.expiry = expiry
        existing.token_data = token_data
    else:
        new_token = CalendarOAuthToken(
            user_id=user.id,
            provider=provider,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            scope=scope,
            expiry=expiry,
            token_data=token_data,
        )
        db.add(new_token)

    db.commit()
