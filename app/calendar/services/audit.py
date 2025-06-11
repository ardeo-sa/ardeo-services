"""
Service utilities for recording audit logs related to meeting activities.

This module defines helper functions to create and persist audit log entries
whenever a user performs an action on a meeting, such as adding notes,
editing content, or uploading files. These logs enable accountability and
historical tracking of user interactions with meeting records.
"""
from sqlalchemy.orm import Session

from app.calendar.models.audit import MeetingAuditLog
from app.users.models.user import User

def log_meeting_action(
    db: Session,
    user: User,
    meeting_id: int,
    action: str,
    object_type: str,
    object_id: int = None,
    meta: dict = None,
):
    """
       Save a meeting audit log entry.

       Logs a specific action taken by a user on a meeting, capturing
       contextual metadata to enable historical tracking and auditing.

       Parameters:
       - db (Session): SQLAlchemy session for database interaction.
       - user (User): The user performing the action.
       - meeting_id (int): The ID of the meeting where the action occurred.
       - action (str): The action performed (e.g., "add_note", "edit_note").
       - object_type (str): The type of object acted upon (e.g., "note", "file").
       - object_id (int, optional): The ID of the affected object.
       - meta (dict, optional): Additional contextual information.
    """
    entry = MeetingAuditLog(
        meeting_id=meeting_id,
        user_id=user.id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        metadata=meta or {}
    )
    db.add(entry)
    db.commit()
