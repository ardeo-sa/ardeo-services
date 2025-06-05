"""
This module defines the `MeetingAuditLog` SQLAlchemy model used for tracking
user actions related to MDT (multidisciplinary team) meetings.

Each record in the `meeting_audit_logs` table represents an audit trail entry,
capturing what action was taken, by whom, on what object, and when. This enables
accountability, traceability, and a historical log of changes or interactions
with meeting-related content.

Fields:
- `meeting_id`: Links the action to a specific meeting.
- `user_id`: Identifies the user who performed the action.
- `action`: Describes the type of activity (e.g., `add_note`, `edit_note`, `upload_file`).
- `object_type`: Indicates the kind of object affected (e.g., `note`, `file`, `meeting`).
- `object_id`: References the specific object instance, if applicable.
- `metadata`: Stores optional additional context (e.g., diff info, filenames).
- `timestamp`: When the action occurred (default: UTC now).

Relationships:
- Connected to `User` and `Meeting` models for relational integrity.

This log is critical for ensuring secure collaboration and traceable updates within MDT workflows.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from app.database.services import Base

class MeetingAuditLog(Base):
    __tablename__ = "meeting_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g., add_note, edit_note, upload_file
    object_type = Column(String, nullable=False)  # e.g., note, file, meeting
    object_id = Column(Integer, nullable=True)
    meta = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    meeting = relationship("Meeting")
