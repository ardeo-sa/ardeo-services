"""
Pydantic schemas for meeting templates.

These schemas define validation rules and serialization
formats for creating, updating, and retrieving meeting templates.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.calendar.enums import TreatmentDecision


class TeamMember(BaseModel):
    """
    Represents a member of the MDT team in a template.

    Attributes:
        user_id (str): GUID of the user.
        role (str): Role of the user in the MDT team (e.g., "chair", "scribe").
    """
    user_id: str = Field(..., description="GUID of the user")
    role: Optional[str] = Field(None, description="Role in the MDT team, e.g. chair, scribe")


class MeetingTemplateBase(BaseModel):
    """
    Shared base schema for meeting templates.

    Attributes:
        speciality (str): The medical speciality of the template.
        hospital (str): The hospital associated with the template.
        location (str): The meeting's location (optional).
        summary_id (str): Reference to summary record in primary schema.
        notes_form_afo_id (str): Reference to AF object form.
        treatment_decision (TreatmentDecision): Controlled vocabulary value for treatment decision.
        virtual_meeting (bool): Indicates if the meeting is virtual.
        team (List[TeamMember]): List of MDT team members.
    """
    title: str
    speciality: str
    hospital: str
    location: Optional[str] = None
    summary_guid: Optional[str] = None
    notes_form_afo_id: Optional[str] = None
    treatment_decision: Optional[TreatmentDecision] = None
    virtual_meeting: bool = False
    team: List[TeamMember] = Field(default_factory=list)
    created_by: Optional[str] = None


class MeetingTemplateCreate(MeetingTemplateBase):
    """
    Schema for creating a new meeting template.
    """
    pass


class MeetingTemplateUpdate(MeetingTemplateBase):
    """
    Schema for updating an existing meeting template.
    """
    pass


class MeetingTemplateResponse(MeetingTemplateBase):
    """
    Schema for returning a meeting template.

    Attributes:
        id (int): Unique identifier of the meeting template.
    """
    id: int

    model_config = {
        "from_attributes": True
    }
