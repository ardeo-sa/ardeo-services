from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database.services import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    notified = Column(Boolean, default=False)
