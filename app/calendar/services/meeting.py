""""
Business logic for meeting operations like creation, participant and subject addition, and note management.
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import or_, and_, select
# from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import Depends, HTTPException

from app.calendar.models.meeting import Meeting, MeetingNote, MeetingParticipant, MeetingPatient
from app.calendar.schemas.meeting import (MeetingCreate, MeetingNoteCreate,
                                          MeetingType, MeetingDetail, MeetingNoteResponse)
from app.users.models.user import User
from app.patients.models.patient import Patient
from app.database.services import get_services_db


async def create_meeting(meeting_data: MeetingCreate, db: AsyncSession = Depends(get_services_db)):
    """
    Create and persist a new meeting with participants and patients (if MDT).

    Args:
        meeting_data (MeetingCreate): Data for the new meeting.
        db (Session): Active SQLAlchemy session.

    Returns:
        Meeting: The created meeting object with relationships.
    """
    new_meeting = Meeting(
        title=meeting_data.title,
        start_time=meeting_data.start_time,
        end_time=meeting_data.end_time,
        type=meeting_data.type.value,
        locked=False,
    )
    db.add(new_meeting)
    await db.flush()

    for user_id in meeting_data.participants:
        db.add(MeetingParticipant(meeting_id=new_meeting.id, user_id=user_id))

    if meeting_data.type == MeetingType.MDT and getattr(meeting_data, 'patient_ids', None):
        for pid in meeting_data.patient_ids:
            db.add(MeetingPatient(meeting_id=new_meeting.id, patient_id=pid))

    await db.commit()
    await db.refresh(new_meeting)

    print(f"Meeting created with id: {new_meeting.id}, title: {new_meeting.title}")
    return new_meeting


async def get_meeting(meeting_id: int, db: AsyncSession, current_user: User) -> Meeting:
    """
    Securely retrieve a meeting with full details, enforcing access control.
    """
    # First check access permission using a lightweight query
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.participants))
        .where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    if current_user.role not in ("admin", "coordinator") and \
            current_user.id not in [p.user_id for p in meeting.participants]:
        raise HTTPException(status_code=403, detail="Access denied.")

    # Fetch full meeting if checks passed
    result = await db.execute(
        select(Meeting)
        .filter_by(id=meeting_id)
        .options(
            selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
            selectinload(Meeting.notes).selectinload(MeetingNote.author),
            selectinload(Meeting.meeting_patients).selectinload(MeetingPatient.patient),
            selectinload(Meeting.patients),
            selectinload(Meeting.supporting_files),
        )
    )

    meeting = result.scalar_one_or_none()
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    return MeetingDetail(
        id=meeting.id,
        title=meeting.title,
        type=meeting.type,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        participants=[p.user_id for p in meeting.participants],
        notes=[
            MeetingNoteResponse(
                id=n.id,
                meeting_id=n.meeting_id,
                author_id=n.author_id,
                type=n.type,
                content=n.content,
                created_at=n.created_at
            )
            for n in meeting.notes
        ],
        locked=meeting.locked
    )


async def add_patients_to_meeting(meeting_id: int, patient_ids: List[int], db: AsyncSession):
    """
        Add one or more patients to the specified MDT meeting.

        Args:
            meeting_id (int): ID of the meeting to update.
            patient_ids (List[int]): List of patient IDs to associate with the meeting.
            db (Session): Database session.

        Returns:
            Meeting: Updated meeting with associated patients.

        Raises:
            HTTPException: If the meeting is not found or is not an MDT.
    """
    result = await db.execute(
        select(Meeting)
        .where(Meeting.id == meeting_id)
        .options(selectinload(Meeting.patients))
    )
    meeting = result.scalar_one_or_none()


    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.type != MeetingType.MDT:
        raise HTTPException(status_code=400, detail="Patients can only be added to MDT meetings")
    if meeting.locked:
        raise HTTPException(status_code=403, detail="Meeting is locked. Cannot add patients.")

    stmt = select(Patient).where(Patient.id.in_(patient_ids))
    result = await db.execute(stmt)
    patients = result.scalars().all()

    meeting.patients.extend(p for p in patients if p not in meeting.patients)
    await db.commit()
    await db.refresh(meeting)
    return meeting


async def add_meeting_note(meeting_id: int, note_data: MeetingNoteCreate, user: User, db: AsyncSession):
    """
        Add a structured note to an MDT meeting.

        Args:
            meeting_id (int): ID of the target meeting.
            note_data (MeetingNoteCreate): Note content and type.
            user (User): The author of the note.
            db (Session): Database session.

        Returns:
            MeetingNote: The newly created note object.

        Raises:
            HTTPException: If the meeting is not found, user not a participant, or meeting is locked.
    """
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.participants).selectinload(MeetingParticipant.user))
        .filter_by(id=meeting_id)
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not any(p.user_id == user.id for p in meeting.participants):
        raise HTTPException(status_code=403, detail="Only participants can add notes")

    if meeting.locked:
        raise HTTPException(status_code=403, detail="Meeting is locked")

    note = MeetingNote(
        meeting_id=meeting.id,
        author_id=user.id,
        type=note_data.type,
        content=note_data.content,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    return note

async def list_meetings(
    db: AsyncSession,
    skip: int,
    limit: int,
    search: Optional[str],
    start_date: Optional[datetime],
    end_date: Optional[datetime]
) -> List[Meeting]:
    """
    Retrieve a paginated and optionally filtered list of meetings.

    Args:
        db (AsyncSession): Database session for executing queries.
        skip (int): Number of records to skip (used for pagination).
        limit (int): Maximum number of records to return (pagination size).
        search (Optional[str]): Search keyword for filtering by title or meeting type.
        start_date (Optional[datetime]): Filter to include only meetings starting on or after this date.
        end_date (Optional[datetime]): Filter to include only meetings ending on or before this date.

    Returns:
        List[Meeting]: A list of meetings matching the provided filters.
    """
    stmt = select(Meeting).options(
        selectinload(Meeting.participants).selectinload(MeetingParticipant.user),
        selectinload(Meeting.meeting_patients).selectinload(MeetingPatient.patient)
    )

    # Dynamic filters
    filters = []

    if search:
        filters.append(
            or_(
                Meeting.title.ilike(f"%{search}%"),
                Meeting.type.ilike(f"%{search}%")
            )
        )

    if start_date:
        filters.append(Meeting.start_time >= start_date)

    if end_date:
        filters.append(Meeting.end_time <= end_date)

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.order_by(Meeting.start_time.desc()).offset(skip).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().unique().all()
