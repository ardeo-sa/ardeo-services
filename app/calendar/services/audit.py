"""
Service utilities for recording audit logs related to meeting activities.

This module defines helper functions to create and persist audit log entries
whenever a user performs an action on a meeting, such as adding notes,
editing content, or uploading files. These logs enable accountability and
historical tracking of user interactions with meeting records.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar.models.audit import MeetingAuditLog
from app.users.models.user import User

logger = logging.getLogger(__name__)

@dataclass
class MeetingAction:
    """Data class to define meeting actions"""
    meeting_id: int
    action: str
    object_type: str
    object_id: Optional[int] = None
    meta: Optional[dict] = None

async def log_meeting_action(
    db: AsyncSession,
    user: User,
    action_data: MeetingAction,
):
    """
   Save a meeting audit log entry.

   Logs a specific action taken by a user on a meeting, capturing
   contextual metadata to enable historical tracking and auditing.

   Args:
        db (Session): SQLAlchemy session for database interaction.
        user (User): The user performing the action.
        action_data (MeetingAction): Details of the action.
           - meeting_id (int): The ID of the meeting where the action occurred.
           - action (str): The action performed (e.g., "add_note", "edit_note").
           - object_type (str): The type of object acted upon (e.g., "note", "file").
           - object_id (int, optional): The ID of the affected object.
           - meta (dict, optional): Additional contextual information.
    """
    logger.info(
        f"User {user.id} performed '{action_data.action}' on "
        f"{action_data.object_type} (ID: {action_data.object_id}) for meeting {action_data.meeting_id}"
    )
    logger.debug(f"Audit metadata: {action_data.meta}")

    entry = MeetingAuditLog(
        meeting_id=action_data.meeting_id,
        user_id=user.id,
        action=action_data.action,
        object_type=action_data.object_type,
        object_id=action_data.object_id,
        metadata=action_data.meta or {}
    )

    try:
        db.add(entry)
        await db.commit()
        logger.info(f"Audit log committed for meeting {action_data.meeting_id}")
    except Exception as e:
        logger.exception(f"Failed to commit audit log for meeting {action_data.meeting_id} {e}")
        raise
