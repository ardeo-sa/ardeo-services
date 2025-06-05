"""
SQLAlchemy model for the `User` entity.

Defines the database representation of users in the system,
including their email, name, and role. The `role` field uses
an enumerated type defined in the user schemas to distinguish
between roles like 'user', 'admin', and 'coordinator'.
"""
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..schemas.user import UserRole
from app.database.services import Base


class User(Base):
    """
       SQLAlchemy model representing a user in the system.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.user, nullable=False)

    calendar_tokens = relationship(
        "CalendarOAuthToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
