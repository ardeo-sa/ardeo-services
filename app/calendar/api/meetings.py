"""
Endpoints for managing calendar meetings, including regular and MDT meetings.
"""
from fastapi import APIRouter

from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.calendar.schemas.meeting import (
    MeetingCreate,
    MeetingResponse,
    MeetingNoteCreate,
    MeetingNoteResponse,
    MeetingDetail,
    MeetingType
)
from app.calendar.services import meeting as services
from app.calendar.models.meeting import Meeting, SupportingFile
from app.core.dependencies import get_current_user, require_role
from app.database.services import get_services_db

from app.users.models.user import User

router = APIRouter()

@router.post("/", response_model=MeetingResponse)
def create_meeting(
    meeting: MeetingCreate,
    db: Session = Depends(get_services_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new meeting (regular or MDT).

    - Regular meetings: Any user can create.
    - MDT meetings: Only coordinators can create.

    Args:
        meeting (MeetingCreate): Payload containing meeting details.
        db (Session): SQLAlchemy DB session.
        current_user (User): Authenticated user from token.

    Returns:
        MeetingResponse: The created meeting object.

    Raises:
        HTTPException: If user attempts to create an MDT meeting without coordinator role.
    """

    if meeting.type == MeetingType.mdt:
        require_role("coordinator")(current_user)

    return services.create_meeting(meeting, db)


@router.get("/{meeting_id}", response_model=MeetingDetail)
def get_meeting(meeting_id: int, db: Session = Depends(get_services_db)):
    """
    Retrieve details of a specific meeting by ID.
    """
    return services.get_meeting(meeting_id, db)


@router.post("/{meeting_id}/patients", response_model=MeetingResponse)
def add_patient_to_meeting(
    meeting_id: int,
    patient_ids: List[int] = Body(...),
    db: Session = Depends(get_services_db),
    current_user: User = Depends(require_role("coordinator")),
):
    """
    Add one or more patients to an MDT meeting.

    Only users with the 'coordinator' role are allowed to perform this action.

    Args:
        meeting_id (int): ID of the MDT meeting.
        patient_ids (List[int]): List of patient IDs to add.
        db (Session): Database session.
        current_user (User): The currently authenticated user.

    Returns:
        MeetingResponse: The updated meeting object including new patients.
    """
    return services.add_patients_to_meeting(meeting_id, patient_ids, db)


@router.post("/{meeting_id}/notes", response_model=MeetingNoteResponse)
def add_note_to_meeting(
    meeting_id: int,
    note: MeetingNoteCreate,
    db: Session = Depends(get_services_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a structured note (e.g., discussion, recommendation) to an MDT meeting.

    Only participants of the meeting may add notes. Locked meetings do not accept new notes.

    Args:
        meeting_id (int): ID of the MDT meeting.
        note (MeetingNoteCreate): The note details (type, content).
        db (Session): Database session.
        current_user (User): The currently authenticated user.

    Returns:
        MeetingNoteResponse: The saved note entry.
    """
    return services.add_meeting_note(meeting_id, note, current_user, db)


@router.post("/{meeting_id}/lock")
def lock_meeting(
    meeting_id: int,
    db: Session = Depends(get_services_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lock a meeting to prevent further changes to its notes or patient list.

    Only users with the 'coordinator' or 'admin' role may lock meetings.

    Args:
        meeting_id (int): ID of the meeting to lock.
        db (Session): Database session.
        current_user (User): The currently authenticated user.

    Returns:
        dict: Confirmation message upon successful lock.
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.role not in ("coordinator", "admin"):
        raise HTTPException(status_code=403, detail="Only coordinators or admins can lock meetings")

    meeting.locked = True
    db.commit()
    return {"detail": f"Meeting {meeting.id} locked."}


@router.get("/{meeting_id}/files/{file_id}", response_class=FileResponse)
def download_supporting_file(
    meeting_id: int,
    file_id: int,
    db: Session = Depends(get_services_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a supporting document attached to an MDT meeting.

    Only meeting participants are allowed to download files.

    Args:
        meeting_id (int): ID of the meeting.
        file_id (int): ID of the file to download.
        db (Session): Database session.
        current_user (User): The currently authenticated user.

    Returns:
        FileResponse: The binary file to download.
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user not in meeting.participants:
        raise HTTPException(status_code=403, detail="Access denied:: Only participants can download files")

    file = db.query(SupportingFile).filter_by(id=file_id, meeting_id=meeting_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=file.path, filename=file.name, media_type='application/octet-stream')


