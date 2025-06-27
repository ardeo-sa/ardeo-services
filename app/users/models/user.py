"""
SQLAlchemy model for the `User` entity.

Defines the database representation of users in the system,
including their email, name, and role. The `role` field uses
an enumerated type defined in the user schemas to distinguish
between roles like 'user', 'admin', and 'coordinator'.
"""
from enum import Enum

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

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

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.NORMAL, nullable=False)
    email = Column(String, nullable=True)
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
    notification_pref = relationship("NotificationPreference",
                                     back_populates="user",
                                     uselist=False,
                                     cascade="all,delete-orphan")

