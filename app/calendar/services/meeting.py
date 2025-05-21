"""
Business logic for meeting operations like creation and retrieval.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.calendar.models import meeting as models
from app.calendar.schemas import meeting as schemas
from app.core.database import get_db

def create_meeting(meeting_data: schemas.MeetingCreate, db: Session = next(get_db())):
    """
    Create and persist a new meeting with participants and patients (if MDT).
    """
    new_meeting = models.Meeting(
        title=meeting_data.title,
        start_time=meeting_data.start_time,
        end_time=meeting_data.end_time,
        type=meeting_data.type.value,
        locked=False,
    )
    db.add(new_meeting)
    db.flush()

    for user_id in meeting_data.participants:
        db.add(models.MeetingParticipant(meeting_id=new_meeting.id, user_id=user_id))

    if meeting_data.type == "mdt" and meeting_data.patient_ids:
        for pid in meeting_data.patient_ids:
            db.add(models.MeetingPatient(meeting_id=new_meeting.id, patient_id=pid))

    db.commit()
    return new_meeting

def get_meeting(meeting_id: int, db: Session = next(get_db())):
    """
    Retrieve a meeting with its full data by ID.
    """
    return db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
