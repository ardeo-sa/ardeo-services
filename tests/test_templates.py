"""
Tests for calendar-related endpoints using template fixtures.
"""
from unittest.mock import patch
import pytest
from httpx import AsyncClient

from app.main import app
from app.core.dependencies import get_current_user
from app.calendar.enums import MeetingType
from tests.fixtures.users import override_user

# from app.calendar.schemas.meeting import MeetingType
from tests.fixtures.meeting_template import mock_meeting_template, shared_meeting_templates

@pytest.mark.asyncio
async def test_get_meetings(mock_meeting, override_current_user_coord, async_client: AsyncClient):
    """
    Test fetching meetings for a coordinator user.
    """
    response = await async_client.get("/api/calendar/meetings/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(str(meeting["id"]) == str(mock_meeting.id) for meeting in data)


@pytest.mark.asyncio
async def test_shared_meeting_access(shared_meeting, normal_user, override_current_user_normal, async_client: AsyncClient):
    """
    Test that a normal user can access a shared meeting.
    """
    response = await async_client.get(f"/api/calendar/meetings/{shared_meeting.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == shared_meeting.id
    assert "Shared Meeting" in data["title"]


@pytest.mark.asyncio
async def test_create_meeting_template_by_coordinator(async_client: AsyncClient, override_current_user_coord):
    """
    Coordinator user can create a meeting template via the API.
    """
    payload = {
        "title": "Weekly MDT template",
        "hospital": "City Hospital",
        "location": "Room 101",
        "speciality": "Oncology",
        "virtual_meeting": True,
        "team": [{"user_id": str(override_current_user_coord.id), "role": "coordinator"}],
        # "created_by": override_current_user_coord.id,
    }

    response = await async_client.post("/api/calendar/meeting-templates/", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == payload["title"]
    assert data["hospital"] == payload["hospital"]
    assert data["location"] == payload["location"]
    assert data["speciality"] == payload["speciality"]
    assert data["virtual_meeting"] == payload["virtual_meeting"]
    # Team should be returned as list of dicts
    assert all(member["user_id"] == str(override_current_user_coord.id) for member in data["team"])


@pytest.mark.asyncio
async def test_create_mdt_meeting_from_template(
        async_client: AsyncClient,
        coordinator_user,
):
    """
    Create an MDT meeting using an existing meeting template.
    """
    app.dependency_overrides[get_current_user] = lambda: coordinator_user

    patcher = patch(
        "app.calendar.services.meeting_template._check_admin_or_coordinator",
        lambda user: None
    )
    patcher.start()

    try:
        # Step 1: Create a template
        template_payload = {
            "title": "Weekly MDT template",
            "hospital": "City Hospital",
            "location": "Room 101",
            "speciality": "Oncology",
            "virtual_meeting": True,
            "team": [{"user_id": str(coordinator_user.id), "role": "coordinator"}],
            "summary_guid": None,
            "notes_form_afo_id": None,
            "treatment_decision": None,
        }

        template_resp = await async_client.post("/api/calendar/meeting-templates/", json=template_payload)
        assert template_resp.status_code == 201
        template_id = template_resp.json()["id"]

        # Step 2: Create meeting using template
        meeting_payload = {
            "template_id": template_id,
            "type": "mdt",
            "start_time": "2030-01-01T09:00:00Z",
            "end_time": "2030-01-01T10:00:00Z",
        }
        meeting_resp = await async_client.post("/api/calendar/meetings/", json=meeting_payload)
        assert meeting_resp.status_code == 200

        meeting_data = meeting_resp.json()
        assert meeting_data["title"] == template_payload["title"]
        assert meeting_data["type"] == "mdt"

        # If participants are returned
        if "participants" in meeting_data:
            participant_ids = [p["id"] for p in meeting_data["participants"]]
            template_user_ids = [member["user_id"] for member in template_payload["team"]]
            assert all(uid in participant_ids for uid in template_user_ids)
    finally:
        patcher.stop()
        app.dependency_overrides.clear()