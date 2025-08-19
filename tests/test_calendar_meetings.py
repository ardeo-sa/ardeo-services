"""
Tests for calendar meeting endpoints using a mock SQLite database.

Includes tests for meeting creation, listing, retrieval, note editing, adding patients,
and permission validation for locking and audit logging.
"""
from datetime import datetime, timedelta, timezone
import pytest
# import tempfile

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from httpx import AsyncClient
# from httpx._transports.asgi import ASGITransport


from app.calendar.models.meeting import Meeting, MeetingParticipant
from app.calendar.schemas.meeting import MeetingType
# from app.users.models.user import User
from app.core.dependencies import get_current_user
from app.main import app
# from app.database.services import get_services_db

@pytest.mark.asyncio
async def test_create_regular_meeting(async_client: AsyncClient, normal_user):
    """
    Test creating a regular meeting by a normal user.
    Normal user is provided by nomrla user fixture
    """
    app.dependency_overrides[get_current_user] = lambda: normal_user

    meeting_data = {
        "title": "Test Regular Meeting",
        "type": MeetingType.REGULAR.value,
        "start_time": "2025-01-01T10:00:00Z",
        "end_time": "2025-01-01T11:00:00Z",
        "locked": False,
        "participants": [normal_user.id]
    }

    # participant_link = MeetingParticipant(user_id=normal_user.id)
    # meeting_data.participants.append(participant_link)

    response = await async_client.post("/api/calendar/meetings/", json=meeting_data)
    print(response.status_code, response.text)

    assert response.status_code == 200
    data = response.json()

    assert data["title"] == meeting_data["title"]
    assert data["type"] == meeting_data["type"]


@pytest.mark.asyncio
async def test_user_is_meeting_participant(normal_user,
                                           db_session: AsyncSession):
    """
    Test that the user is correctly added as a participant to a meeting.
    """
    # Simulate authentication
    # app.dependency_overrides[get_current_user] = lambda: normal_user

    # Sync with session
    normal_user = await db_session.merge(normal_user)

    # Create meeting with the user as a participant
    meeting = Meeting(
        title="Test Meeting",
        type=MeetingType.MDT.value,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        participants=[
            MeetingParticipant(user=normal_user)
        ],
        locked=False
    )
    db_session.add(meeting)
    await db_session.commit()
    await db_session.refresh(meeting)

    # Fetch meeting from DB and verify participant inclusion
    result = await db_session.execute(
        select(Meeting).
        options(selectinload(Meeting.participants).
        selectinload(MeetingParticipant.user)).
        where(Meeting.id == meeting.id)
    )
    fetched_meeting = result.scalar_one()

    participant_ids = {p.user_id for p in fetched_meeting.participants}
    assert normal_user.id in participant_ids


@pytest.mark.asyncio
async def test_list_meetings(async_client: AsyncClient):
    """
    Test that listing meetings returns valid meeting data.
    """
    response = await async_client.get("/api/calendar/meetings/")
    assert response.status_code == 200

    meetings = response.json()
    assert isinstance(meetings, list)


@pytest.mark.asyncio
async def test_get_meeting_by_id(async_client: AsyncClient, normal_user,
                                 db_session: AsyncSession):
    """
    Test retrieving a meeting by its ID.
    """
    # Simulate authenticated user
    app.dependency_overrides[get_current_user] = lambda: normal_user

    normal_user = await db_session.merge(normal_user)

    # Prepare meeting and user fixture
    meeting = Meeting(
        title="Test Meeting",
        type=MeetingType.MDT.value,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(hours=1),
        participants=[
            MeetingParticipant(user=normal_user)
        ],
        locked=False
    )
    db_session.add(meeting)
    await db_session.commit()
    await db_session.refresh(meeting)

    response = await async_client.get(f"/api/calendar/meetings/{meeting.id}")
    assert response.status_code == 200

    meeting_data = response.json()
    assert meeting_data["id"] == meeting.id
    assert "title" in meeting_data
