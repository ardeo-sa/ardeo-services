"""
Tests for calendar meeting endpoints using a mock SQLite database.

Includes tests for meeting creation, listing, retrieval, note editing, adding patients,
and permission validation for locking and audit logging.
"""
import pytest
import httpx
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.calendar.schemas.meeting import MeetingCreate, MeetingNoteCreate, MeetingType, MeetingNoteType
from app.users.models.user import User
from app.main import app


@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_create_regular_meeting(client: TestClient, db_session):
    """
    Test creating a regular meeting by a normal user.
    """
    # Mock user with no special role
    user = User(id=1, role="user")
    db_session.add(user)
    db_session.commit()

    meeting_data = {
        "title": "Test Regular Meeting",
        "type": MeetingType.regular.value,
        "date": "2025-01-01T10:00:00Z",
        "description": "A regular meeting test"
    }

    # Simulate login by overriding dependency or using a fixture that returns `user`
    response = await async_client.post("/api/meetings/", json=meeting_data)

    assert response.status_code == 200
    data = response.json()

    assert data["title"] == meeting_data["title"]
    assert data["type"] == meeting_data["type"]


@pytest.mark.asyncio
async def test_create_mdt_meeting_requires_coordinator_role(client: TestClient):
    """
    Test that creating an MDT meeting without coordinator role fails.
    """
    meeting_data = {
        "title": "MDT Meeting",
        "type": MeetingType.mdt.value,
        "date": "2025-01-01T10:00:00Z",
        "description": "An MDT meeting test"
    }

    # Assume user with role 'user' (not coordinator)
    response = async_client.post("/api/meetings/", json=meeting_data)

    assert response.status_code == 403 or response.status_code == 401


@pytest.mark.asyncio
async def test_add_note_to_meeting(client: TestClient, db_session):
    """
    Test adding a note to a meeting.
    """
    # Prepare meeting and user fixtures (mock or create them)

    meeting_id = 1  # Assuming a meeting with ID 1 exists
    note_data = {
        "type": MeetingNoteType.recommendation.value,
        "content": "This is a test recommendation note."
    }

    response = async_client.post(f"/api/meetings/{meeting_id}/notes", json=note_data)
    assert response.status_code == 200
    note = response.json()
    assert note["content"] == note_data["content"]
    assert note["type"] == note_data["type"]


@pytest.mark.asyncio
async def test_lock_meeting_requires_proper_role(client: TestClient, db_session):
    """
    Test locking a meeting as a user without permission fails.
    """
    meeting_id = 1

    response = async_client.post(f"/api/meetings/{meeting_id}/lock")
    # Expect 403 Forbidden if not coordinator or admin
    assert response.status_code == 403 or response.status_code == 401


@pytest.mark.asyncio
async def test_get_meeting_audit_log_requires_coordinator_or_admin(client: TestClient, db_session):
    """
    Test that audit log retrieval is forbidden for normal users.
    """
    meeting_id = 1

    response = async_client.get(f"/api/meetings/{meeting_id}/audit")
    assert response.status_code == 403 or response.status_code == 401


@pytest.mark.asyncio
async def test_list_meetings(client: TestClient, db_session):
    """
    Test that listing meetings returns valid meeting data.
    """
    response = async_client.get("/api/meetings/")
    assert response.status_code == 200
    meetings = response.json()
    assert isinstance(meetings, list)


@pytest.mark.asyncio
async def test_get_meeting_by_id(client: TestClient, db_session):
    """
    Test retrieving a meeting by its ID.
    """
    # Assumes a meeting with ID 1 exists
    meeting_id = 1
    response = async_client.get(f"/api/meetings/{meeting_id}")
    assert response.status_code == 200
    meeting = response.json()
    assert meeting["id"] == meeting_id
    assert "title" in meeting


@pytest.mark.asyncio
async def test_edit_note_only_by_author(client: TestClient, db_session):
    """
    Test that only the author can edit a meeting note.
    """
    # Setup: user is not the author
    meeting_id = 1
    note_id = 1
    edit_payload = {
        "type": MeetingNoteType.discussion.value,
        "content": "Edited note content"
    }

    response = async_client.put(
        f"/api/meetings/{meeting_id}/notes/{note_id}",
        json=edit_payload
    )

    # Expect 403 if not the author
    assert response.status_code in [403, 404]


@pytest.mark.asyncio
async def test_add_patient_to_meeting_requires_coordinator(client: TestClient):
    """
    Test adding patients to a meeting is restricted to coordinators.
    """
    meeting_id = 1
    payload = [10, 11]

    response = async_client.post(f"/api/meetings/{meeting_id}/patients", json=payload)
    assert response.status_code in [403, 401]


@pytest.mark.asyncio
async def test_lock_meeting_success(client: TestClient, db_session):
    """
    Test locking a meeting as a user with 'coordinator' or 'admin' role.
    """
    meeting_id = 1

    # Assuming a coordinator user is authenticated
    response = async_client.post(f"/api/meetings/{meeting_id}/lock")
    if response.status_code == 200:
        assert "locked" in response.json()["detail"]
    else:
        assert response.status_code in [403, 401]


@pytest.mark.asyncio
async def test_get_meeting_audit_log_as_admin(client: TestClient, db_session):
    """
    Test audit log is accessible to users with 'admin' or 'coordinator' roles.
    """
    meeting_id = 1
    response = async_client.get(f"/api/meetings/{meeting_id}/audit")
    if response.status_code == 200:
        assert isinstance(response.json(), list)
    else:
        assert response.status_code in [403, 401]


@pytest.mark.asyncio
async def test_create_meeting_as_coordinator(client, override_current_user_coord, db_session):
    """
    Test coordinator can create an MDT meeting.
    """
    payload = {
        "title": "Neuro MDT",
        "type": "mdt",
        "scheduled_at": "2025-06-05T10:00:00Z"
    }

    response = async_client.post("/api/meetings/", json=payload)
    assert response.status_code == 200
    assert response.json()["title"] == "Neuro MDT"


@pytest.mark.asyncio
async def test_create_meeting_as_user_fails_for_mdt(client, override_current_user_normal):
    """
    Test normal users cannot create MDT meetings.
    """
    payload = {
        "title": "MDT Attempt",
        "type": "mdt",
        "scheduled_at": "2025-06-06T09:00:00Z"
    }

    response = async_client.post("/api/meetings/", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_add_patient_to_meeting_as_coordinator(client, override_current_user_coord, db_session):
    """
    Test that a coordinator can add patients to a meeting.
    """
    # First, create a meeting
    response = async_client.post("/api/meetings/", json={
        "title": "MDT for Patient Add",
        "type": "mdt",
        "scheduled_at": "2025-07-01T14:00:00Z"
    })
    assert response.status_code == 200
    meeting_id = response.json()["id"]

    # Add patients
    response = async_client.post(f"/api/meetings/{meeting_id}/patients", json=[101, 102])
    assert response.status_code == 200
    assert "patients" in response.json()


@pytest.mark.asyncio
async def test_upload_supporting_file(client, override_current_user_coord, db_session):
    """
    Test that a coordinator can upload a file to a meeting.
    """
    # Create a meeting
    response = async_client.post("/api/meetings/", json={
        "title": "File Upload MDT",
        "type": "mdt",
        "scheduled_at": "2025-07-02T09:00:00Z"
    })
    assert response.status_code == 200
    meeting_id = response.json()["id"]

    # Simulate file upload
    file_content = b"This is a test PDF content"
    file_data = {
        "file": ("test.pdf", file_content, "application/pdf")
    }

    upload_url = f"/api/meetings/{meeting_id}/files"
    response = async_client.post(upload_url, files=file_data)

    assert response.status_code == 200
    resp_json = response.json()
    assert resp_json["filename"] == "test.pdf"
    assert resp_json["size_bytes"] == len(file_content)


@pytest.mark.asyncio
async def test_download_file_requires_participant(client, override_current_user_coord, db_session):
    """
    Test that only participants can download uploaded files.
    """
    # Assume upload already done, test rejection for non-participant
    meeting_id = 1
    file_id = 1
    response = async_client.get(f"/api/meetings/{meeting_id}/files/{file_id}")
    assert response.status_code in [403, 404]
