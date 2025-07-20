"""
SQLAlchemy models for meeting data including meeting details,
participants, notes, and patients discussed in MDT.
"""
from datetime import datetime, timezone
from enum import Enum
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLEnum

from app.database.services import Base
from app.calendar.enums import MeetingType, MeetingNoteType


class Meeting(Base):
    """
    Represents a scheduled meeting (regular or MDT).
    """
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    type = Column(SQLEnum(MeetingType), nullable=False)
    locked = Column(Boolean, default=False)
    external_event_id = Column(String, nullable=True, unique=True)
    external_provider = Column(String, nullable=True)  # "google" or "microsoft"

    participants = relationship("MeetingParticipant", back_populates="meeting")
    notes = relationship("MeetingNote", back_populates="meeting")
    meeting_patients = relationship("MeetingPatient", back_populates="meeting", cascade="all, delete-orphan")
    patients = relationship("Patient", secondary="meeting_patients", viewonly=True, back_populates="meetings")


class MeetingParticipant(Base):
    """
    Links users to meetings as participants.
    """
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    user_id = Column(String, ForeignKey("users.id"))
    # user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    meeting = relationship("Meeting", back_populates="participants")
    user = relationship("User", back_populates="meeting_links")


class MeetingNote(Base):
    """
    Notes taken during MDT meetings with categories like discussion or conclusion.
    """
    __tablename__ = "meeting_notes"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    type = Column(SQLEnum(MeetingNoteType), nullable=False)
    content = Column(Text)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(), # pylint: disable=not-callable
        nullable=False)
    author_id = Column(String, ForeignKey("users.id"))
    meeting = relationship("Meeting", back_populates="notes")
    author = relationship("User")


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


class MDTAssignment(Base):
    """
    Tracks MDT-specific assignments for users,
    used to trigger notifications and manage responsibilities.
    """
    __tablename__ = "mdt_assignments"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    role = Column(String, nullable=True)  # Optional role (e.g. scribe, chair)
    assigned_at = Column(DateTime(timezone=True), default=func.now())
    notified = Column(Boolean, default=False)  # For notification tracking

    meeting = relationship("Meeting", backref="mdt_assignments")
    user = relationship("User", backref="mdt_assignments")

    def __repr__(self):
        return f"<MDTAssignment(meeting_id={self.meeting_id}, user_id={self.user_id}, role={self.role})>"
