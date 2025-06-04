"""
SQLAlchemy models for meeting data including meeting details,
participants, notes, and patients discussed in MDT.
"""
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship

from app.database.services import Base


class Meeting(Base):
    """
    Represents a scheduled meeting (regular or MDT).
    """
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    type = Column(String, nullable=False)  # "regular" or "mdt"
    locked = Column(Boolean, default=False)

    participants = relationship("MeetingParticipant", back_populates="meeting")
    notes = relationship("MeetingNote", back_populates="meeting")
    meeting_patients = relationship("MeetingPatient", back_populates="meeting", cascade="all, delete-orphan")
    patients = relationship("Patient", secondary="meeting_patients", viewonly=True, back_populates="meetings")


class MeetingType(str, Enum):
    MDT = "mdt"
    REVIEW = "review"


class MeetingParticipant(Base):
    """
    Links users to meetings as participants.
    """
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    user_id = Column(Integer)

    meeting = relationship("Meeting", back_populates="participants")


class MeetingNote(Base):
    """
    Notes taken during MDT meetings with categories like discussion or conclusion.
    """
    __tablename__ = "meeting_notes"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    type = Column(String)
    content = Column(Text)
    created_at = Column(DateTime)

    meeting = relationship("Meeting", back_populates="notes")


class MeetingPatient(Base):
    """
    Patients associated with MDT meetings.
    """
    __tablename__ = "meeting_patients"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"))

    meeting = relationship("Meeting", back_populates="meeting_patients")
    patient = relationship("Patient", back_populates="meeting_links")


class SupportingFile(Base):
    """
    Represents a file uploaded to a meeting (e.g., reports, attachments).
    """
    __tablename__ = "supporting_files"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String)
    is_encrypted = Column(Boolean, default=False)
    encryption_method = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    meeting = relationship("Meeting", backref="supporting_files")
