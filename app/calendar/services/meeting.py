""""
Business logic for meeting operations like creation, participant and subject addition, and note management.
"""
from typing import List
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from app.calendar.models.meeting import Meeting, MeetingNote, MeetingParticipant, MeetingPatient
from app.calendar.schemas.meeting import MeetingCreate, MeetingNoteCreate, MeetingNoteType, MeetingType
from app.users.models import User
from app.patients.models import Patient
from app.database.services import get_services_db
from datetime import datetime


def create_meeting(meeting_data: MeetingCreate, db: Session = Depends(get_services_db)):
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
    db.flush()

    for user_id in meeting_data.participants:
        db.add(MeetingParticipant(meeting_id=new_meeting.id, user_id=user_id))

    if meeting_data.type == MeetingType.mdt and getattr(meeting_data, 'patient_ids', None):
        for pid in meeting_data.patient_ids:
            db.add(MeetingPatient(meeting_id=new_meeting.id, patient_id=pid))

    db.commit()
    db.refresh(new_meeting)
    return new_meeting

def get_meeting(meeting_id: int, db: Session):
    """
    Retrieve a meeting with its full data by ID.

    Args:
        meeting_id (int): Unique meeting identifier.
        db (Session): Database session.

    Returns:
        Meeting | None: Meeting if found, otherwise None.
    """
    return db.query(Meeting).filter(Meeting.id == meeting_id).first()

def add_patients_to_meeting(meeting_id: int, patient_ids: List[int], db: Session):
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
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.type != MeetingType.mdt:
        raise HTTPException(status_code=400, detail="Patients can only be added to MDT meetings")

    patients = db.query(Patient).filter(Patient.id.in_(patient_ids)).all()
    meeting.patients.extend(p for p in patients if p not in meeting.patients)
    db.commit()
    db.refresh(meeting)
    return meeting

def add_meeting_note(meeting_id: int, note_data: MeetingNoteCreate, user: User, db: Session):
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
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
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
    db.commit()
    db.refresh(note)
    return note
