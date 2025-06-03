from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

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

    #token_data = Column(JSON, nullable=True) # use only for testing

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="calendar_tokens")
