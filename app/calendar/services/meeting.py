""""
Business logic for meeting operations like creation, participant and subject addition, and note management.
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import or_, and_, select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException

from app.calendar.models.meeting import Meeting, MeetingNote, MeetingParticipant, MeetingPatient
from app.calendar.schemas.meeting import MeetingCreate, MeetingNoteCreate, MeetingNoteType, MeetingType
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

    if meeting_data.type == MeetingType.mdt and getattr(meeting_data, 'patient_ids', None):
        for pid in meeting_data.patient_ids:
            db.add(MeetingPatient(meeting_id=new_meeting.id, patient_id=pid))

    await db.commit()
    await db.refresh(new_meeting)

    print(f"Meeting created with id: {new_meeting.id}, title: {new_meeting.title}")
    return new_meeting

async def get_meeting(meeting_id: int, db: Session):
    """
    Retrieve a meeting with its full data by ID.

    Args:
        meeting_id (int): Unique meeting identifier.
        db (Session): Database session.

    Returns:
        Meeting | None: Meeting if found, otherwise None.
    """

    result = await db.execute(select(Meeting).filter_by(id=meeting_id))
    meeting = result.scalar_one_or_none()
    return meeting

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
    result = await db.execute(select(Meeting).filter_by(id=meeting_id))
    meeting = result.scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.type != MeetingType.mdt:
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
    result = await db.execute(select(Meeting).filter_by(id=meeting_id))
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if user not in meeting.participants:
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
