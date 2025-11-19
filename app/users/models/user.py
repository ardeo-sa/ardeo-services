"""
SQLAlchemy model for the `User` entity.

Defines the database representation of users in the system,
including their email, name, and role. The `role` field uses
an enumerated type defined in the user schemas to distinguish
between roles like 'user', 'admin', and 'coordinator'.
"""
from enum import Enum
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.notifications.models import WatchedItem
from app.users.schemas.user import UserRole
from app.database.services import Base


class UserRole(str, Enum):
    """Possible user roles"""
    ADMIN = "admin"
    COORDINATOR = "coordinator"
    NORMAL = "normal"


class User(Base):
    """
       SQLAlchemy model representing a user in the system.
    """
    __tablename__ = "users"

    # id = Column(Integer, primary_key=True, index=True)
    # id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.NORMAL, nullable=False)
    whatsapp_number = Column(String, nullable=True)

    @property
    def name(self) -> str:
        """Dynamically combines first_name and last_name every time name is required"""
        return f"{self.first_name} {self.last_name}"

    calendar_tokens = relationship(
        "CalendarOAuthToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    meeting_links = relationship("MeetingParticipant", back_populates="user")
    watched_items = relationship("WatchedItem", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notification_pref = relationship("NotificationPreference", back_populates="user", uselist=False,  cascade="all,delete-orphan")
    meetings_created = relationship("Meeting", back_populates="creator")
    templates_created = relationship("MeetingTemplate", back_populates="creator")