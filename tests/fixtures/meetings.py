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
from app.calendar.models.meeting import Meeting, MeetingParticipant

from tests.fixtures.users import normal_user, coordinator_user # pylint: disable=unused-import


@pytest_asyncio.fixture
async def mock_meeting(db_session, coordinator_user):
    """
    Create a sample meeting for testing.
    """
    now = datetime.now(timezone.utc)
    meeting = Meeting(
        title="MDT Session",
        start_time=now,
        end_time=now + timedelta(hours=1),
        type=MeetingType.MDT,
        created_by=coordinator_user.id
    )
    # Add coordinator as participant
    meeting.participants.append(MeetingParticipant(user_id=coordinator_user.id))

    db_session.add(meeting)
    await db_session.commit()
    return meeting


@pytest_asyncio.fixture
async def shared_meeting(db_session, normal_user, coordinator_user):
    """
    Meeting shared among multiple participants.
    """
    now = datetime.now(timezone.utc)
    meeting = Meeting(
        title="Shared Meeting",
        start_time=now,
        end_time=now + timedelta(hours=1),
        type=MeetingType.MDT,
        created_by=coordinator_user.id
    )
    meeting.participants.append(MeetingParticipant(user=normal_user))
    meeting.participants.append(MeetingParticipant(user=coordinator_user))

    db_session.add(meeting)
    await db_session.commit()
    await db_session.refresh(meeting)
    return meeting
