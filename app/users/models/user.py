from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Column, Integer, String
from ..schemas.user import UserRole

class User(Base):
    """
       SQLAlchemy model representing a user in the system.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.user, nullable=False)
