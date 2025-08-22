"""
Meeting-related test fixtures.

Includes:
- Single mock meeting
- Shared meetings
- Meetings with multiple participants
"""
# pylint: disable=redefined-outer-name
from datetime import datetime, timezone, timedelta
import pytest_asyncio

from app.calendar.enums import MeetingType
from app.calendar.models.meeting import Meeting

from tests.fixtures.users import normal_user, coordinator_user # pylint: disable=unused-import


@pytest_asyncio.fixture
async def mock_meeting(db_session, coordinator_user):
    """
    Create a sample meeting for testing.
    """
    session = db_session
    coord = coordinator_user
    now = datetime.now(timezone.utc)
    meeting = Meeting(
        title="MDT Session",
        start_time=now,
        end_time=now + timedelta(hours=1),
        type=MeetingType.MDT,
        created_by=coord.id
    )
    session.add(meeting)
    await session.commit()
    return meeting


@pytest_asyncio.fixture
async def shared_meeting(db_session, coordinator_user):
    """
    Meeting shared among multiple participants.
    """
    meeting = Meeting(
        title="Shared Meeting",
        type="team",
        created_by=coordinator_user.id
    )
    db_session.add(meeting)
    await db_session.commit()
    await db_session.refresh(meeting)
    return meeting


@pytest_asyncio.fixture
async def meeting_with_participants(db_session, shared_meeting, normal_user, coordinator_user):
    """
    Attach multiple participants to a shared meeting.
    """
    shared_meeting.participants.append(normal_user)
    shared_meeting.participants.append(coordinator_user)
    db_session.add(shared_meeting)
    await db_session.commit()
    await db_session.refresh(shared_meeting)
    return shared_meeting
