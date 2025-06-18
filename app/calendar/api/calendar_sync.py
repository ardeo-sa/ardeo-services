"""API endpoints for calendar synchronization operations."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.services import get_services_db
from app.users.models.user import User
from app.core.dependencies import get_current_user
from app.calendar.services import calendar_sync

router = APIRouter()

@router.get("/sync", tags=["Calendar"])
def sync_calendar_events(
    db: Session = Depends(get_services_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sync upcoming events from user's connected external calendar.
    Returns events pulled from Google or Microsoft.
    """
    try:
        events = calendar_sync.sync_user_calendar(current_user, db)
        return {"events": events}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync calendar: {e}") from e


@router.post("/push/{meeting_id}", tags=["Calendar"])
def push_meeting(
    meeting_id: int,
    db: Session = Depends(get_services_db),
    current_user: User = Depends(get_current_user)
):
    """
    Push a meeting to the user's external calendar (Google or Microsoft).
    """
    try:
        result = calendar_sync.push_meeting_to_external(meeting_id, current_user, db)
        return {"status": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to push meeting: {e}") from e
