"""
SQLAlchemy models for meeting data including meeting details,
participants, notes, and patients discussed in MDT.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Float, CheckConstraint
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
    patients = relationship("MeetingPatient", back_populates="meeting")


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
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    patient_id = Column(Integer)

    meeting = relationship("Meeting", back_populates="patients")



class SupportingFile(Base):
    """
    Files attached to MDT meetings (e.g., reports, imaging, documents).
    """
    __tablename__ = "supporting_files"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    file_size = Column(Float, nullable=False)  # File size in bytes, required
    mime_type = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploader_id = Column(Integer, nullable=True)

    # Storage and access
    storage_provider = Column(String, nullable=True)  # e.g. 'local', 's3'
    storage_url = Column(String, nullable=True)

    # Encryption metadata
    is_encrypted = Column(Boolean, default=False)
    encryption_method = Column(String, nullable=True)  # e.g. 'AES-256', 'GPG'

    # Constraints
    __table_args__ = (
        CheckConstraint('file_size <= 10 * 1024 * 1024', name='check_file_size_max_10mb'),  # Max 10MB
    )

    meeting = relationship("Meeting", backref="files")

