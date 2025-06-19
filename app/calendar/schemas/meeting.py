"""
Pydantic schemas for meetings, including creation, response models,
notes, and meeting metadata.
"""
from typing import List, Optional
from datetime import datetime

# from sqlalchemy import Column, ForeignKey, Integer
# from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from app.calendar.enums import MeetingType, MeetingNoteType


class MeetingCreate(BaseModel):
    """
    Schema for creating a new meeting.
    """
    title: str = Field(..., json_schema_extra={"example":"Weekly MDT"}, min_length=3)
    type: MeetingType = Field(..., json_schema_extra={"example":"mdt"})
    start_time: datetime = Field(..., json_schema_extra={"example":"2024-06-15T10:00:00Z"})
    end_time: datetime = Field(..., json_schema_extra={"example":"2024-06-15T11:00:00Z"})
    participants: List[int] = Field(..., json_schema_extra={"example":[2, 3]})
    patients: Optional[List[int]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Liver MDT Discussion",
                "type": "mdt",
                "start_time": "2024-06-15T10:00:00Z",
                "end_time": "2024-06-15T11:00:00Z",
                "participants": [2, 5, 9]
            }
        }
    }


class MeetingResponse(BaseModel):
    """
    Basic meeting response.
    """
    id: int
    title: str
    type: MeetingType
    start_time: datetime
    end_time: datetime

    model_config = {
        "from_attributes": True
    }


class MeetingNoteResponse(BaseModel):
    """
    Schema for meeting note response
    """
    id: int
    meeting_id: int
    type: str
    content: str
    created_at: datetime
    author_id: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


class MeetingNotes(BaseModel):
    """
    Aggregated response for a list of notes, if needed as a standalone response.
    """
    meeting_id: int
    notes: List[MeetingNoteResponse]


class UserOut(BaseModel):
    """
    Output schema for a user (participant).
    """
    id: int
    full_name: Optional[str] = None
    email: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class PatientOut(BaseModel):
    """
    Output schema for a patient in a meeting.
    """
    id: int
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime] = None
    identifier: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class MeetingDetail(MeetingResponse):
    """
    Detailed meeting response with participants, notes, patients, and lock status.
    """
    participants: List[UserOut] = Field(default_factory=list)
    notes: List[MeetingNoteResponse] = Field(default_factory=list)
    patients: List[PatientOut] = Field(default_factory=list)
    locked: bool

    model_config = {
        "from_attributes": True
    }


class MeetingNoteCreate(BaseModel):
    """
        Schema for creating a new meeting note.

        Fields:
        - `type`: The classification of the note (e.g., discussion, recommendation, conclusion).
        - `content`: The text content of the note (minimum 1 character).
    """
    type: MeetingNoteType = Field(..., description="Type of note")
    content: str = Field(..., min_length=1, description="Note content")

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "recommendation",
                "content": "Consider MRI follow-up within 3 months."
            }
        }
    }


class MeetingNoteUpdate(BaseModel):
    """
    Edit meeting note
    """
    type: MeetingNoteType
    content: str


