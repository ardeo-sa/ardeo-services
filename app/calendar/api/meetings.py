"""
Endpoints for managing calendar meetings, including regular and MDT meetings.
"""
from uuid import uuid4
import os
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.responses import FileResponse
from fastapi import File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar.schemas.meeting import (
    MeetingCreate,
    MeetingResponse,
    MeetingNoteCreate,
    MeetingNoteResponse,
    MeetingDetail,
    MeetingType
)
from app.calendar.services import meeting as services
from app.calendar.models.meeting import Meeting, SupportingFile, MeetingNote, MeetingFormLock
from app.calendar.models.audit import MeetingAuditLog
from app.core.dependencies import get_current_user, require_role, require_coordinator
from app.database.services import get_services_db
from app.calendar.services.audit import MeetingAction, log_meeting_action
from app.users.models.user import User
from app.calendar.schemas.meeting import MeetingNoteUpdate

MAX_FILE_SIZE_MB = 100
UPLOAD_DIR = "/tmp/uploads"


router = APIRouter()


@router.post("/", response_model=MeetingResponse)
async def create_meeting(
    meeting: MeetingCreate,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new meeting (regular or MDT).

    - Regular meetings: Any user can create.
    - MDT meetings: Only coordinators can create.

    Args:
        meeting (MeetingCreate): Payload containing meeting details.
        db (AsyncSession): SQLAlchemy DB async session.
        current_user (User): Authenticated user from token.

    Returns:
        MeetingResponse: The created meeting object.

    Raises:
        HTTPException: If user attempts to create an MDT meeting without coordinator role.
    """

    if meeting.type == MeetingType.MDT:
        require_role("coordinator")(current_user)

    return await services.create_meeting(meeting, db)


@router.get("/{meeting_id}", response_model=MeetingDetail)
async def get_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve details of a specific meeting by ID.
    """
    # if current_user.role not in ("admin", "coordinator"):
    #     raise HTTPException(status_code=403, detail="Access denied.")

    return await services.get_meeting(meeting_id, db, current_user)


@router.post("/{meeting_id}/patients", response_model=MeetingResponse)
async def add_patient_to_meeting(
    meeting_id: int,
    patient_ids: List[int] = Body(...),
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(require_coordinator), # pylint: disable=unused-argument
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
    return await services.add_patients_to_meeting(meeting_id, patient_ids, db)


@router.post("/{meeting_id}/notes", response_model=MeetingNoteResponse)
async def add_note_to_meeting(
    meeting_id: int,
    note: MeetingNoteCreate,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a structured note (e.g., discussion, recommendation) to an MDT meeting.

    Notes may optionally belong to a structured form (e.g., 'decision_to_treat', 'mdt_discussion').
    If a form has been locked, no additional notes can be added to that form.

    Only participants of the meeting may add notes. Locked meetings do not accept new notes.

    Args:
        meeting_id (int): ID of the MDT meeting.
        note (MeetingNoteCreate): The note details (type, content).
        db (Session): Database session.
        current_user (User): The currently authenticated user.

    Returns:Raises:
        HTTPException: If the form or meeting is locked, or user lacks permission.
        MeetingNoteResponse: The saved note entry.

    Raises:
        HTTPException: If the form or meeting is locked, or user lacks permission.
    """
    # Check for form-level lock
    if note.form_name:
        result = await db.execute(
            select(MeetingFormLock)
            .filter_by(meeting_id=meeting_id, form_name=note.form_name)
        )
        locked = result.scalar_one_or_none()
        if locked:
            raise HTTPException(status_code=403, detail=f"Notes for form '{note.form_name}' are locked.")

    meeting_note = await services.add_meeting_note(meeting_id, note, current_user, db)

    action = MeetingAction(
        meeting_id=meeting_id,
        action="add_note",
        object_type="note",
        object_id=meeting_note.id,
        meta={
            "type": note.type,
            "form_name": note.form_name
        }
    )
    await log_meeting_action(db, current_user, action)

    return meeting_note


@router.put("/{meeting_id}/notes/{note_id}", response_model=MeetingNoteResponse)
async def edit_note_to_meeting(
    meeting_id: int,
    note_id: int,
    note: MeetingNoteUpdate,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user)
):
    """
    Edit a note in an MDT meeting.

    Only the original author may edit their note.
    Locked meetings do not allow edits to general notes.
    Locked forms do not allow edits to notes tied to that form.

    Args:
        meeting_id (int): ID of the MDT meeting.
        note_id (int): ID of the note to edit.
        note (MeetingNoteUpdate): The new values for the note.
        db (Session): Database session.
        current_user (User): The currently authenticated user.

    Returns:
        MeetingNoteResponse: The updated note object.

    Raises:
        HTTPException: If the meeting/note is not found, locked, or user not authorized.
    """
    result = await db.execute(select(Meeting).filter_by(id=meeting_id))
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.locked:
        raise HTTPException(status_code=403, detail="Meeting is locked. Notes cannot be edited.")

    result = await db.execute(select(MeetingNote).filter_by(id=note_id, meeting_id=meeting_id))
    note_obj = result.scalar_one_or_none()
    if not note_obj:
        raise HTTPException(status_code=404, detail="Note not found")

    if note_obj.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own notes.")

    # Check if the form associated with the note is locked
    if note_obj.form_name:
        result = await db.execute(
            select(MeetingFormLock)
            .filter_by(meeting_id=meeting_id, form_name=note_obj.form_name)
        )
        locked = result.scalar_one_or_none()
        if locked:
            raise HTTPException(status_code=403, detail=f"Notes for form '{note_obj.form_name}' are locked.")

    note_obj.type = note.type
    note_obj.content = note.content
    await db.commit()
    await db.refresh(note_obj)
    return MeetingNoteResponse.from_orm(note_obj)


@router.post("/{meeting_id}/lock")
async def lock_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_services_db),
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
    result = await db.execute(select(Meeting).filter_by(id=meeting_id))
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.role not in ("coordinator", "admin"):
        raise HTTPException(status_code=403, detail="Only coordinators or admins can lock meetings")

    meeting.locked = True
    await db.commit()

    action = MeetingAction(
        meeting_id=meeting_id,
        action="lock_meeting",
        object_type="note",
    )
    await log_meeting_action(db, current_user, action)

    return {"detail": f"Meeting {meeting.id} locked."}



@router.post("/{meeting_id}/files", response_model=dict)
async def upload_supporting_file(
    meeting_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_services_db),
    current_user = Depends(require_role("coordinator", "admin")),
):
    """
    Upload a supporting file for an MDT meeting.
    Only coordinators or admins are allowed to upload.
    Validates file size (max 10MB) and stores it with metadata.
    current_user (User): Authenticated user with allowed role.

    Args:
        meeting_id (int): Target meeting ID.
        file (UploadFile): The uploaded file.
        db (Session): Database session.
        current_user (User): Authenticated user with allowed role.

    Returns:
        dict: Confirmation and file metadata.
    """
    result = await db.execute(select(Meeting).filter_by(id=meeting_id))
    meeting = result.scalar_one_or_none()

    # Check if meeting exists
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    # Enforce lock check
    if meeting.locked:
        raise HTTPException(status_code=403, detail="Meeting is locked. Uploads are not allowed.")

    # Generate unique file path and save file
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Stream file to disk and check size
    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    total_size = 0
    with open(filepath, "wb") as out_file:
        while chunk := file.file.read(1024 * 1024):  # 1MB chunks
            total_size += len(chunk)
            if total_size > max_size_bytes:
                out_file.close()
                os.remove(filepath)
                raise HTTPException(status_code=400, detail="File exceeds 10MB limit")
            out_file.write(chunk)

    # Create DB record
    file_record = SupportingFile(
        meeting_id=meeting_id,
        name=file.filename,
        path=filepath,
        file_size=total_size,
        mime_type=file.content_type,
        is_encrypted=False,
        encryption_method=None,
    )
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)

    action = MeetingAction(
        meeting_id=meeting_id,
        action="upload_file",
        object_type="file",
        object_id=file_record.id,
        meta={"filename": file.filename, "size": file_record.file_size}
    )
    await log_meeting_action(db, current_user, action)

    return {
        "file_id": file_record.id,
        "filename": file_record.name,
        "size_bytes": file_record.file_size,
        "mime_type": file_record.mime_type,
        "uploaded_by": current_user.id,
        "uploaded_at": file_record.uploaded_at.isoformat()
    }


@router.get("/{meeting_id}/files/{file_id}", response_class=FileResponse)
async def download_supporting_file(
    meeting_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_services_db),
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
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.participants))
        .where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()

    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.id not in [p.id for p in meeting.participants]:
        raise HTTPException(status_code=403, detail="Access denied:: Only participants can download files")

    result = await db.execute(select(SupportingFile).filter_by(id=file_id, meeting_id=meeting_id))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=file.path, filename=file.name, media_type='application/octet-stream')



@router.get("/", response_model=List[MeetingResponse])
async def list_meetings(
    db: AsyncSession = Depends(get_services_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, le=100, description="Max number of records to return"),
    search: Optional[str] = Query(None, description="Search term to filter by title or type"),
    start_date: Optional[datetime] = Query(None, description="Start of date range"),
    end_date: Optional[datetime] = Query(None, description="End of date range"),
):
    """
    List meetings with optional pagination and search.

    Args:
        db (Session): DB session.
        skip (int): Number of records to skip.
        limit (int): Number of records to return.
        search (str, optional): Filter string for meeting title or type.
        start_date (datetime, optional): Filter meetings starting on or after this date.
        end_date (datetime, optional): Filter meetings ending on or before this date.

    Returns:
        List[MeetingResponse]: A list of meetings.
    """

    return await services.list_meetings(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/{meeting_id}/audit", response_model=List[dict])
async def get_meeting_audit_log(
    meeting_id: int,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve audit logs for a meeting. Only coordinators/admins can view.
    """
    if current_user.role not in ("coordinator", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    stmt = (
        select(MeetingAuditLog)
        .filter_by(meeting_id=meeting_id)
        .order_by(MeetingAuditLog.timestamp.desc())
    )

    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [
        {
            "user_id": log.user_id,
            "action": log.action,
            "object_type": log.object_type,
            "object_id": log.object_id,
            "timestamp": log.timestamp.isoformat(),
            "metadata": log.metadata,
        }
        for log in logs
    ]


@router.post("/{meeting_id}/forms/{form_name}/lock")
async def lock_meeting_form_notes(
    meeting_id: int,
    form_name: str,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(require_role("coordinator", "admin")),
):
    """
    Lock a specific form's notes (e.g., 'decision_to_treat') for a meeting.

    Args:
        meeting_id (int): The ID of the MDT meeting.
        form_name (str): The name of the form to lock.

    Returns:
        dict: Confirmation message.
    """
    exists_stmt = select(MeetingFormLock).filter_by(meeting_id=meeting_id, form_name=form_name)
    result = await db.execute(exists_stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail=f"Form '{form_name}' is already locked")

    lock = MeetingFormLock(
        meeting_id=meeting_id,
        form_name=form_name,
        locked_by=current_user.id
    )
    db.add(lock)
    await db.commit()

    action = MeetingAction(
        meeting_id=meeting_id,
        action="lock_form_notes",
        object_type="form_note",
        meta={"form_name": form_name}
    )
    await log_meeting_action(db, current_user, action)

    return {"detail": f"Form '{form_name}' notes locked."}


@router.post("/{meeting_id}/notes/{note_id}/retract", response_model=MeetingNoteResponse)
async def retract_meeting_note(
    meeting_id: int,
    note_id: int,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retract a note (e.g., in MDT discussion) by crossing it out.

    Only the original author may retract their note. Retracted notes are not deleted and remain in history.

    Args:
        meeting_id (int): ID of the meeting.
        note_id (int): ID of the note to retract.
        db (Session): Database session.
        current_user (User): The currently authenticated user.

    Returns:
        MeetingNoteResponse: The updated (retracted) note.
    """
    result = await db.execute(select(MeetingNote).filter_by(id=note_id, meeting_id=meeting_id))
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You can only retract your own notes")
    if note.is_retracted:
        raise HTTPException(status_code=400, detail="Note is already retracted")

    note.is_retracted = True
    await db.commit()
    await db.refresh(note)

    action = MeetingAction(
        meeting_id=meeting_id,
        action="retract_note",
        object_type="note",
        object_id=note.id,
        meta={"form_name": note.form_name, "note_type": note.type}
    )
    await log_meeting_action(db, current_user, action)

    return MeetingNoteResponse.from_orm(note)


@router.post("/{meeting_id}/notes/{note_id}/unretract", response_model=MeetingNoteResponse)
async def unretract_meeting_note(
    meeting_id: int,
    note_id: int,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user),
):
    """
    Undo a previous retraction of a meeting note.

    Only the original author may unretract a previously retracted note.
    """
    result = await db.execute(select(MeetingNote).filter_by(id=note_id, meeting_id=meeting_id))
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You can only unretract your own notes")
    if not note.is_retracted:
        raise HTTPException(status_code=400, detail="Note is not currently retracted")

    note.is_retracted = False
    await db.commit()
    await db.refresh(note)

    action = MeetingAction(
        meeting_id=meeting_id,
        action="unretract_note",
        object_type="note",
        object_id=note.id,
        meta={"form_name": note.form_name, "note_type": note.type}
    )
    await log_meeting_action(db, current_user, action)

    return MeetingNoteResponse.from_orm(note)

@router.post("/{meeting_id}/actions")
async def record_meeting_action(
    meeting_id: int,
    action: str = Body(..., description="Description of the action (free text or predefined type)"),
    metadata: Optional[dict] = Body(None),
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user)
):
    """
    Record a freeform meeting action not tied to a form or patient.

    Useful for tracking decisions, attendance, or other events that aren't notes.

    Args:
        meeting_id (int): ID of the meeting.
        action (str): Action description.
        metadata (dict, optional): Additional metadata (e.g. user, timestamp, context).

    Returns:
        dict: Confirmation with logged data.
    """
    result = await db.execute(select(Meeting).filter_by(id=meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    meeting_action = MeetingAction(
        meeting_id=meeting_id,
        action=action,
        object_type="custom_action",
        meta=metadata or {}
    )
    await log_meeting_action(db, current_user, meeting_action)

    return {"detail": f"Action '{action}' recorded", "metadata": metadata}
