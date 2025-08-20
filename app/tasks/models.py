"""
Module defining the Task model for the application.

This module contains the SQLAlchemy model for tasks, including the table
structure and relationships for assigning tasks to users.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database.services import Base


class Task(Base):
    """
    Represents a task in the system.

    Attributes:
        id (int): Primary key for the task.
        title (str): Title or name of the task.
        assignee_id (int): Foreign key referencing the assigned user.
        notified (bool): Flag indicating if the assignee has been notified.
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notified = Column(Boolean, default=False)
