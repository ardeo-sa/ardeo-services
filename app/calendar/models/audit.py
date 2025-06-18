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
    """
       Represents an audit log entry for actions performed on meetings.

       This model records who performed an action (user), what the action was
       (e.g., adding or editing a note, uploading a file), and on which object
       type and ID it occurred. Useful for tracking changes and maintaining
       a history of user interactions with meeting-related resources.

       Attributes:
           id (int): Primary key.
           meeting_id (int): ID of the related meeting.
           user_id (int): ID of the user who performed the action.
           action (str): Type of action (e.g., 'add_note', 'edit_note').
           object_type (str): Type of object affected ('note', 'file', 'meeting').
           object_id (int): ID of the object affected.
           meta (JSON): Optional metadata about the action.
           timestamp (datetime): Time when the action occurred.
    """
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
