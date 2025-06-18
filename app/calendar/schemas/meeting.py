"""
Pydantic schemas for meetings, including creation, response models,
notes, and meeting metadata.
"""
from enum import Enum
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

class MeetingType(str, Enum):
    """
        Enum representing the type of meeting.

        Options:
        - `regular`: A standard meeting with general discussions.
        - `mdt`: A multidisciplinary team (MDT) meeting involving collaborative decision-making across specialties.
    """
    regular = "regular"
    mdt = "mdt"


class MeetingCreate(BaseModel):
    """
    Schema for creating a new meeting.
    """
    title: str = Field(..., example="Weekly MDT", min_length=3)
    type: MeetingType = Field(..., example="mdt")
    start_time: datetime = Field(..., example="2024-06-15T10:00:00Z")
    end_time: datetime = Field(..., example="2024-06-15T11:00:00Z")
    participants: List[int] = Field(..., example=[2, 3])
    patients: Optional[List[int]] = None

    class Config:
        schema_extra = {
            "example": {
                "title": "Liver MDT Discussion",
                "type": "mdt",
                "start_time": "2024-06-15T10:00:00Z",
                "end_time": "2024-06-15T11:00:00Z",
                "participants": [2, 5, 9]
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


class MeetingNoteType(str, Enum):
    """
        Enum representing the type of note taken during a meeting.

        Options:
        - `discussion`: General discussion points.
        - `recommendation`: Suggestions or advice based on discussion.
        - `conclusion`: Final decisions or outcomes from the meeting.
    """
    discussion = "discussion"
    recommendation = "recommendation"
    conclusion = "conclusion"


class MeetingNoteResponse(BaseModel):
    """
    Schema for meeting note response
    """
    id: int
    meeting_id: int
    author_id: int
    type: MeetingNoteType
    content: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class MeetingNotes(BaseModel):
    """
    Aggregated response for a list of notes, if needed as a standalone response.
    """
    meeting_id: int
    notes: List[MeetingNoteResponse]


class MeetingDetail(MeetingResponse):
    """
    Detailed meeting response with participants, notes, and lock status.
    """
    participants: List[int]
    notes: List[MeetingNoteResponse]
    locked: bool


class MeetingNoteCreate(BaseModel):
    """
        Schema for creating a new meeting note.

        Fields:
        - `type`: The classification of the note (e.g., discussion, recommendation, conclusion).
        - `content`: The text content of the note (minimum 1 character).
    """
    type: MeetingNoteType = Field(..., description="Type of note")
    content: str = Field(..., min_length=1, description="Note content")

    class Config:
        schema_extra = {
            "example": {
                "type": "recommendation",
                "content": "Consider MRI follow-up within 3 months."
            }
        }


class MeetingNoteUpdate(BaseModel):
    """
    Edit meeting note
    """
    type: MeetingNoteType
    content: str
