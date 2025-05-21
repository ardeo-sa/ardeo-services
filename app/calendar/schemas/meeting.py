"""
Pydantic schemas for meetings, including creation, response models,
notes, and meeting metadata.
"""
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from enum import Enum

class MeetingType(str, Enum):
    regular = "regular"
    mdt = "mdt"


class NoteBase(BaseModel):
    """
    Base fields for meeting notes.
    """
    content: str
    type: str  # e.g., "discussion", "recommendation", "conclusion"

class NoteCreate(NoteBase):
    """
    Schema for creating a new note.
    """
    pass

class Note(NoteBase):
    """
    Returned note object with metadata.
    """
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class MeetingCreate(BaseModel):
    """
    Schema for creating a new meeting.
    """
    title: str
    start_time: datetime
    end_time: datetime
    type: MeetingType
    participants: List[int]
    patient_ids: Optional[List[int]] = None

class MeetingResponse(BaseModel):
    """
    Basic meeting response.
    """
    id: int
    title: str
    type: str
    start_time: datetime
    end_time: datetime

class MeetingDetail(MeetingResponse):
    """
    Detailed meeting response with participants, notes, and lock status.
    """
    participants: List[int]
    notes: List[Note]
    locked: bool
