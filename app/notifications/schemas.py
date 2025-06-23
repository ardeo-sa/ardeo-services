"""
Defines the Pydantic models (schemas) for validating and serializing notification data.
"""
from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel

from app.notifications.enums import NotificationType, NotificationStatus

class NotificationBase(BaseModel):
    """Base schema shared by all Notification schemas."""
    user_id: int
    message: str
    type: NotificationType = NotificationType.IN_APP
    patient_id: Optional[int]
    pathway_step_id: Optional[int]
    task_id: Optional[int]

class NotificationCreate(BaseModel):
    """Schema for creating a new Notification."""
    user_id: int
    message: str
    type: NotificationType
    patient_id: Optional[int] = None
    pathway_step_id: Optional[int] = None
    task_id: Optional[int] = None

class NotificationRead(NotificationBase):
    """Schema for reading a Notification from the database."""
    id: int
    status: NotificationStatus
    created_at: datetime
    sent_at: Optional[datetime]
    read_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }

class NotificationOut(BaseModel):
    """Schema for serializing notification data to API consumers."""
    id: int
    user_id: int
    message: str
    type: NotificationType
    status: NotificationStatus
    created_at: datetime
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    snooze_until: Optional[datetime]  # <-- Add this

    model_config = {
        "from_attributes": True
    }


class WatchedItemCreate(BaseModel):
    """
        Schema for creating a new WatchedItem.

        Attributes:
            user_id (int): ID of the user setting the watch.
            item_type (str): Type of item (e.g., 'form', 'metric').
            item_id (int): Unique identifier of the item to watch.
            trigger_conditions (dict, optional): Rules for when to trigger a notification.
    """
    user_id: int
    item_type: str
    item_id: int
    trigger_conditions: Optional[Dict] = None