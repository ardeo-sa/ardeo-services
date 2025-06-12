"""
notifications.schemas

Defines the Pydantic models (schemas) for validating and serializing notification data.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from .enums import NotificationType, NotificationStatus

class NotificationBase(BaseModel):
    """Base schema shared by all Notification schemas."""
    user_id: int
    message: str
    type: NotificationType = NotificationType.IN_APP
    patient_id: Optional[int]
    pathway_step_id: Optional[int]
    task_id: Optional[int]

class NotificationCreate(NotificationBase):
    """Schema for creating a new Notification."""
    pass

class NotificationRead(NotificationBase):
    """Schema for reading a Notification from the database."""
    id: int
    status: NotificationStatus
    created_at: datetime
    sent_at: Optional[datetime]
    read_at: Optional[datetime]

    class Config:
        orm_mode = True
