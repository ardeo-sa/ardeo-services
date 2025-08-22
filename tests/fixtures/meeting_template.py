"""
MeetingTemplate-related test fixtures.

Includes:
- Single mock template
- Shared templates (with different hospitals/specialities)
"""
# pylint: disable=redefined-outer-name

import pytest_asyncio

from app.calendar.models.meeting_template import MeetingTemplate
from tests.fixtures.users import coordinator_user, admin_user  # pylint: disable=unused-import


@pytest_asyncio.fixture
async def mock_meeting_template(db_session, coordinator_user):
    """
    Create a sample meeting template for testing.
    """
    template = MeetingTemplate(
        summary="Weekly MDT template",
        hospital="City Hospital",
        speciality="Oncology",
        created_by=coordinator_user.id,
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest_asyncio.fixture
async def shared_meeting_templates(db_session, admin_user):
    """
    Create multiple templates under different configurations.
    """
    templates = [
        MeetingTemplate(
            summary="Surgical Review",
            hospital="General Hospital",
            speciality="Surgery",
            created_by=admin_user.id,
        ),
        MeetingTemplate(
            summary="Cardiology Case Review",
            hospital="City Hospital",
            speciality="Cardiology",
            created_by=admin_user.id,
        ),
    ]
    db_session.add_all(templates)
    await db_session.commit()
    for t in templates:
        await db_session.refresh(t)
    return templates
