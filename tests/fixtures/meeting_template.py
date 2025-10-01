"""
MeetingTemplate-related test fixtures.

Includes:
- Single mock template
- Shared meetings (with different hospitals/specialities)
- Meetings with multiple participants
"""
# pylint: disable=redefined-outer-name
# from datetime import datetime, timezone, timedelta
import pytest_asyncio

from app.calendar.models.meeting_template import MeetingTemplate
# from app.calendar.enums import MeetingType
# from app.calendar.models.meeting import Meeting, MeetingParticipant

from tests.fixtures.users import coordinator_user, admin_user  # pylint: disable=unused-import


@pytest_asyncio.fixture
async def mock_meeting_template(db_session, coordinator_user):
    """
    Create a sample meeting template for testing.
    """
    template = MeetingTemplate(
        title="Weekly MDT template",
        hospital="City Hospital",
        location="Room 101",
        speciality="Oncology",
        created_by=coordinator_user.id,
        virtual_meeting=True,
        team=[{"role": "coordinator", "user_id": coordinator_user.id}],
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest_asyncio.fixture
async def shared_meeting_templates(db_session, coordinator_user):
    """
    Create multiple templates under different configurations.
    """
    templates = [
        MeetingTemplate(
            title="Surgical Review",
            hospital="General Hospital",
            speciality="Surgery",
            created_by=coordinator_user.id,
        ),
        MeetingTemplate(
            title="Cardiology Case Review",
            hospital="City Hospital",
            speciality="Cardiology",
            created_by=coordinator_user.id,
        ),
    ]
    db_session.add_all(templates)
    await db_session.commit()
    for t in templates:
        await db_session.refresh(t)
    return templates
