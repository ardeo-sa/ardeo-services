"""
Pydantic schemas for meetings, including creation, response models,
notes, and meeting metadata.
"""
from typing import List, Optional, Any
from datetime import datetime
# from uuid import UUID

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
    # participants: List[int] = Field(..., json_schema_extra={"example":[2, 3]})
    # patients: Optional[List[int]] = None
    participants: List[str] = Field(..., json_schema_extra={"example": [
        "8ae75201-d9c0-4f8a-a8ae-996797d8e7fe",
        "c6199d07-98e2-472f-9df9-fcc050f8ce18"
    ]})
    patients: Optional[List[str]] = Field(
        default=None,
        json_schema_extra={"example": [
            "a7f3aa3e-9214-45c3-87f1-e356c3b4c6d2",
            "9d2a128f-1efb-42c5-8b94-b5e2b73d8d4b"
        ]}
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Liver MDT Discussion",
                "type": "mdt",
                "start_time": "2024-06-15T10:00:00Z",
                "end_time": "2024-06-15T11:00:00Z",
                # "participants": [2, 5, 9]
                "participants": [
                    "8ae75201-d9c0-4f8a-a8ae-996797d8e7fe",
                    "c6199d07-98e2-472f-9df9-fcc050f8ce18"
                ],
                "patients": [
                    "a7f3aa3e-9214-45c3-87f1-e356c3b4c6d2"
                ]
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
    id: str
    meeting_id: int
    type: str
    form_name: Optional[str]
    content: dict[str, Any]
    created_at: datetime
    author_id: Optional[str] = None
    is_retracted: bool = Field(False, description="Indicates whether the note was retracted by the author")

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
    id: str = Field(..., json_schema_extra={"example": "0070e402-ad27-4fca-957f-dd7727c9fa52"})
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
        - `form_name`: Name of the form in which the note was made
        - `content`: The text content of the note (minimum 1 character).
    """
    type: MeetingNoteType = Field(..., description="Type of note")
    form_name: Optional[str] = Field(None, description="Name of the form this note is associated with")
    content: dict = Field(..., description="Note content as structured data")

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "recommendation",
                "content": {"decision": "start chemo", "date": "2025-08-01"},
                "form_name": "decision_to_treat"
            }
        }
    }


class MeetingNoteUpdate(BaseModel):
    """
    Edit meeting note
    """
    type: MeetingNoteType = Field(..., description="Type of note")
    content: dict = Field(..., description="Note content as structured data")
    form_name: Optional[str] = Field(None, description="Name of the form this note is associated with")
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "recommendation",
                    "content": {
                        "decision": "start chemo",
                        "date": "2025-08-01"
                    },
                    "form_name": "decision_to_treat"
                }
            ]
        }
    }

