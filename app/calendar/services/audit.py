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
    metadata: dict = None,
):
    """
    Save a meeting audit log.
    """
    entry = MeetingAuditLog(
        meeting_id=meeting_id,
        user_id=user.id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        metadata=metadata or {}
    )
    db.add(entry)
    db.commit()
