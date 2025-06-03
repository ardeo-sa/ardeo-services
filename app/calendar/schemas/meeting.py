"""
Pydantic schemas for meetings, including creation, response models,
notes, and meeting metadata.
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional
from datetime import datetime

class MeetingType(str, Enum):
    regular = "regular"
    mdt = "mdt"

class MeetingNoteType(str, Enum):
    discussion = "discussion"
    recommendation = "recommendation"
    conclusion = "conclusion"

class MeetingNoteCreate(BaseModel):
    type: MeetingNoteType = Field(..., description="Type of note")
    content: str = Field(..., min_length=1, description="Note content")

    class Config:
        schema_extra = {
            "example": {
                "type": "recommendation",
                "content": "Consider MRI follow-up within 3 months."
            }
        }

class MeetingCreate(BaseModel):
    """
    Schema for creating a new meeting.
    """
    title: str = Field(..., example="Weekly MDT", min_length=3)
    type: MeetingType = Field(..., example="mdt")
    start_time: datetime = Field(..., example="2024-06-15T10:00:00Z")
    end_time: datetime = Field(..., example="2024-06-15T11:00:00Z")
    participant_ids: List[int] = Field(..., example=[2, 3])
    patient_ids: Optional[List[int]] = None

    class Config:
        schema_extra = {
            "example": {
                "title": "Liver MDT Discussion",
                "type": "mdt",
                "start_time": "2024-06-15T10:00:00Z",
                "end_time": "2024-06-15T11:00:00Z",
                "participant_ids": [2, 5, 9]
            }
        }


class MeetingNoteResponse(BaseModel):
    id: int
    meeting_id: int
    author_id: int
    type: MeetingNoteType
    content: str
    created_at: datetime


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

class MeetingNoteUpdate(BaseModel):
    """
    Edit meeting note
    """
    type: str
    content: str
