"""
Endpoints for managing calendar meetings, including regular and MDT meetings.
"""
from fastapi import APIRouter
from app.calendar.schemas import meeting as schemas
from app.calendar.services import meeting as services

router = APIRouter()

@router.post("/", response_model=schemas.MeetingResponse)
def create_meeting(meeting: schemas.MeetingCreate):
    """
    Create a new meeting (regular or MDT).
    """
    return services.create_meeting(meeting)

@router.get("/{meeting_id}", response_model=schemas.MeetingDetail)
def get_meeting(meeting_id: int):
    """
    Retrieve details of a specific meeting by ID.
    """
    return services.get_meeting(meeting_id)
