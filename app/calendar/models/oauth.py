"""
This module defines the SQLAlchemy model for storing OAuth tokens associated
with external calendar providers such as Google and Microsoft.

The `CalendarOAuthToken` table captures essential token data including:
- The associated user (foreign key to users table)
- The calendar provider ("google" or "microsoft")
- Access and refresh tokens
- Token type, scope, and expiration datetime
- Creation timestamp for audit and lifecycle management

This model supports secure and persistent storage of calendar authentication
credentials, enabling features like event sync or calendar access on behalf of
users.

Relationships:
- Linked to the `User` model via a many-to-one relationship.

Notes:
- The `token_data` JSON column is commented out and can be used optionally
  for storing raw token responses (useful during development or debugging).
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Text, JSON
from sqlalchemy.orm import relationship

from app.database.services import Base

class CalendarOAuthToken(Base):
    """
    Stores OAuth tokens for external calendar providers (Google, Microsoft).
    """
    __tablename__ = "calendar_oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # "google" or "microsoft"
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String, nullable=True)
    scope = Column(String, nullable=True)
    expiry = Column(DateTime, nullable=True)
    token_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # user = relationship("User", back_populates="calendar_tokens")

