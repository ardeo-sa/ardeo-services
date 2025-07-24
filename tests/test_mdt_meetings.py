"""
Tests for MDT meeting endpoints using a mock SQLite database.

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
from app.calendar.schemas.meeting import MeetingType, MeetingNoteType
# from app.users.models.user import User
from app.core.dependencies import get_current_user
from app.main import app
# from app.database.services import get_services_db


@pytest.mark.asyncio
async def test_create_mdt_meeting(async_client: AsyncClient, coordinator_user):
    """
    Test creating a regular meeting by a normal user.
    Normal user is provided by nomrla user fixture
    """
    app.dependency_overrides[get_current_user] = lambda: coordinator_user

    try:
        meeting_data = {
            "title": "Test MDT Meeting",
            "type": MeetingType.MDT.value,
            "start_time": "2025-01-01T10:00:00Z",
            "end_time": "2025-01-01T11:00:00Z",
            "participants": [coordinator_user.id],
            "locked": False
        }

        response = await async_client.post("/api/calendar/meetings/", json=meeting_data)
        print(response.status_code, response.text)

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == meeting_data["title"]
        assert data["type"] == meeting_data["type"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_mdt_meeting_requires_coordinator_role(async_client: AsyncClient,
                                                            normal_user):
    """
    Test that creating an MDT meeting without coordinator role fails.
    """
    # Simulate authenticated user
    app.dependency_overrides[get_current_user] = lambda: normal_user

    meeting_data = {
        "title": "Test MDT Meeting set-up by regular user",
        "type": MeetingType.MDT.value,
        "start_time": "2025-01-01T10:00:00Z",
        "end_time": "2025-01-01T11:00:00Z",
        "participants": [normal_user.id],
        "locked": False
    }

    # Assume user with role 'user' (not coordinator)
    response = await async_client.post("/api/calendar/meetings/", json=meeting_data)
    print(response.status_code, response.text)

    assert response.status_code in {403, 401}


@pytest.mark.asyncio
async def test_add_note_to_meeting(
        async_client: AsyncClient,
        normal_user,
        db_session: AsyncSession,
        # override_current_user_normal # pylint: disable=unused-argument
):
    """
    Test adding a note to a meeting.
    """
    app.dependency_overrides[get_current_user] = lambda: normal_user
    try:
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

        note_data = {
            "type": MeetingNoteType.RECOMMENDATION.value,
            "form_name": "decision_to_treat",
            "content": {
                "decision": "start chemo",
                "date": "2025-08-01",
            }
        }

        response = await async_client.post(f"/api/calendar/meetings/{meeting.id}/notes", json=note_data)

        assert response.status_code == 200
        note = response.json()
        # print(note["form_name"])
        # print(note)
        assert note["form_name"] == "decision_to_treat"
        assert note["content"]["decision"] == "start chemo"
        # assert note["content"] == note_data["content"]
        assert note["type"] == note_data["type"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_edit_note_only_by_author(async_client: AsyncClient, normal_user,
                                        db_session: AsyncSession):
    """
    Test that only the author can edit a meeting note.
    """
    # Setup: user is not the author
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

    note_id = 1
    edit_payload = {
        "type": MeetingNoteType.DISCUSSION.value,
        "content": {
            "text": "Edited note content"
        }
    }

    response = await async_client.put(
        f"/api/calendar/meetings/{meeting.id}/notes/{note_id}",
        json=edit_payload
    )

    # Expect 403 if not the author
    assert response.status_code in [403, 404]


@pytest.mark.asyncio
async def test_lock_meeting_success(async_client: AsyncClient, coordinator_user, db_session: AsyncSession):
    """
    Test locking a meeting as a user with 'coordinator' or 'admin' role.
    """
    # Simulate authenticated coordinator
    app.dependency_overrides[get_current_user] = lambda: coordinator_user

    try:
        coordinator_user = await db_session.merge(coordinator_user)

        # Prepare meeting fixture
        meeting = Meeting(
            title="Test Meeting",
            type=MeetingType.MDT.value,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            participants=[
                MeetingParticipant(user=coordinator_user)
            ],
            locked=False
        )
        db_session.add(meeting)
        await db_session.commit()
        await db_session.refresh(meeting)

        # Assuming a coordinator user is authenticated
        response = await async_client.post(f"/api/calendar/meetings/{meeting.id}/lock")
        if response.status_code == 200:
            assert "locked" in response.json()["detail"]
        else:
            assert response.status_code in [403, 401]
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_lock_meeting_requires_proper_role(async_client: AsyncClient, normal_user,
                                                 db_session: AsyncSession):
    """
    Test locking a meeting as a user without permission fails.
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

    response = await async_client.post(f"/api/calendar/meetings/{meeting.id}/lock")

    # Expect 403 Forbidden if not coordinator or admin
    assert response.status_code in {403, 401}


@pytest.mark.asyncio
async def test_add_patient_to_meeting_as_coordinator(async_client: AsyncClient, coordinator_user,
                                                     db_session:AsyncSession):
    """
    Test that a coordinator can add patients to a meeting.
    """
    app.dependency_overrides[get_current_user] = lambda: coordinator_user

    try:
        coordinator_user = await db_session.merge(coordinator_user)

        # Prepare meeting fixture
        meeting = Meeting(
            title="Test Meeting",
            type=MeetingType.MDT.value,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            participants=[
                MeetingParticipant(user=coordinator_user)
            ],
            locked=False
        )
        db_session.add(meeting)
        await db_session.commit()
        await db_session.refresh(meeting)

        # Add patients
        response = await async_client.post(f"/api/calendar/meetings/{meeting.id}/patients", json=[101, 102])
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_add_patient_to_meeting_requires_coordinator(
        async_client: AsyncClient,
        normal_user,
        db_session: AsyncSession
):
    """
    Test adding patients to a meeting is restricted to coordinators.
    """
    # Simulate authenticated user
    app.dependency_overrides[get_current_user] = lambda: normal_user

    normal_user = await db_session.merge(normal_user)

    # Prepare meeting fixture
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

    payload = [10, 11]

    response = await async_client.post(f"/api/calendar/meetings/{meeting.id}/patients", json=payload)
    assert response.status_code in [403, 401]


@pytest.mark.asyncio
async def test_upload_supporting_file(async_client: AsyncClient, coordinator_user,
                                      db_session:AsyncSession):
    """
    Test that a coordinator can upload a file to a meeting.
    """
    # Simulate authenticated user
    app.dependency_overrides[get_current_user] = lambda: coordinator_user
    try:
        coordinator_user = await db_session.merge(coordinator_user)

        # Create a meeting
        meeting = Meeting(
            title="Test Meeting",
            type=MeetingType.MDT.value,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            participants=[
                MeetingParticipant(user=coordinator_user)
            ],
            locked=False
        )
        db_session.add(meeting)
        await db_session.commit()
        await db_session.refresh(meeting)

        # Simulate file upload
        file_content = b"This is a test PDF content"
        file_data = {
            "file": ("test.pdf", file_content, "application/pdf")
        }

        upload_url = f"/api/calendar/meetings/{meeting.id}/files"
        response = await async_client.post(upload_url, files=file_data)

        assert response.status_code == 200
        resp_json = response.json()
        assert resp_json["filename"] == "test.pdf"
        assert resp_json["size_bytes"] == len(file_content)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_meeting_audit_log_as_admin(async_client: AsyncClient, coordinator_user, db_session: AsyncSession):
    """
    Test audit log is accessible to users with 'admin' or 'coordinator' roles.
    """
    app.dependency_overrides[get_current_user] = lambda: coordinator_user

    try:
        coordinator_user = await db_session.merge(coordinator_user)

        # Prepare meeting fixture
        meeting = Meeting(
            title="Test Meeting",
            type=MeetingType.MDT.value,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            participants=[
                MeetingParticipant(user=coordinator_user)
            ],
            locked=False
        )
        db_session.add(meeting)
        await db_session.commit()
        await db_session.refresh(meeting)

        response = await async_client.get(f"/api/calendar/meetings/{meeting.id}/audit")
        if response.status_code == 200:
            assert isinstance(response.json(), list)
        else:
            assert response.status_code in [403, 401]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_meeting_audit_log_requires_coordinator_or_admin(async_client: AsyncClient, normal_user,
                                                                   db_session: AsyncSession):
    """
    Test that audit log retrieval is forbidden for normal users.
    """
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

    response = await async_client.get(f"/api/calendar/meetings/{meeting.id}/audit")
    assert response.status_code in {403, 401}


@pytest.mark.asyncio
async def test_post_meeting_action_success(async_client: AsyncClient, coordinator_user, db_session: AsyncSession):
    """Coordinator records a meeting action."""
    app.dependency_overrides[get_current_user] = lambda: coordinator_user
    try:
        coordinator_user = await db_session.merge(coordinator_user)

        meeting = Meeting(
            title="Action Test",
            type=MeetingType.MDT.value,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            participants=[MeetingParticipant(user=coordinator_user)],
            locked=False
        )
        db_session.add(meeting)
        await db_session.commit()
        await db_session.refresh(meeting)

        action_data = {
            "action": "attendance_marked",
            "metadata": {"location": "Zoom"}
        }

        response = await async_client.post(
            f"/api/calendar/meetings/{meeting.id}/actions", json=action_data
        )

        assert response.status_code == 200
        assert "Action" in response.json()["detail"]
        # assert response.json()["detail"] == action_data["action"]
        assert response.json()["metadata"] == {"location": "Zoom"}

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_retract_note(async_client: AsyncClient, normal_user, db_session: AsyncSession):
    """Test that a note author can retract their message."""
    app.dependency_overrides[get_current_user] = lambda: normal_user
    try:
        normal_user = await db_session.merge(normal_user)
        meeting = Meeting(
            title="Retract Note Test",
            type=MeetingType.MDT.value,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            participants=[MeetingParticipant(user=normal_user)],
            locked=False
        )
        db_session.add(meeting)
        await db_session.commit()
        await db_session.refresh(meeting)

        # Add a note
        response = await async_client.post(
            f"/api/calendar/meetings/{meeting.id}/notes",
            json={"type": "discussion", "content": {
            "decision": "Note to be retracted"
        }}
        )
        note_id = response.json()["id"]

        # Retract it
        retract_response = await async_client.post(
            f"/api/calendar/meetings/{meeting.id}/notes/{note_id}/retract"
        )
        # print(retract_response.json())
        assert retract_response.status_code == 200
        assert retract_response.json()["is_retracted"] is True
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_restore_note(async_client: AsyncClient, normal_user, db_session: AsyncSession):
    """Test undoing a retraction of a note."""
    app.dependency_overrides[get_current_user] = lambda: normal_user
    try:
        normal_user = await db_session.merge(normal_user)
        meeting = Meeting(
            title="Restore Note Test",
            type=MeetingType.MDT.value,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            participants=[MeetingParticipant(user=normal_user)],
            locked=False
        )
        db_session.add(meeting)
        await db_session.commit()
        await db_session.refresh(meeting)

        # Create a note
        response = await async_client.post(
            f"/api/calendar/meetings/{meeting.id}/notes",
            json={"type": "discussion", "content": {
                "decision": "Note to be restored"
            }}
        )
        print("dupa")
        # print(response.json())
        note_id = response.json()["id"]
        # print(note_id)

        # Retract it
        retract_response = await async_client.post(
            f"/api/calendar/meetings/{meeting.id}/notes/{note_id}/retract"
        )
        print(retract_response.json())

        # Restore it
        restore_response = await async_client.post(
            f"/api/calendar/meetings/{meeting.id}/notes/{note_id}/restore"
        )
        print(restore_response.json())

        assert restore_response.status_code == 200
        assert restore_response.json()["is_retracted"] is False
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_locking_prevents_note_edit(async_client: AsyncClient, coordinator_user, db_session: AsyncSession):
    """Once locked, no further notes should be editable."""
    app.dependency_overrides[get_current_user] = lambda: coordinator_user
    try:
        coordinator_user = await db_session.merge(coordinator_user)
        meeting = Meeting(
            title="Lock + Edit Test",
            type=MeetingType.MDT.value,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=1),
            participants=[MeetingParticipant(user=coordinator_user)],
            locked=False
        )
        db_session.add(meeting)
        await db_session.commit()
        await db_session.refresh(meeting)

        note_data = {
            "type": MeetingNoteType.RECOMMENDATION.value,
            "form_name": "decision_to_treat",
            "content": {
                "decision": "start chemo",
                "date": "2025-08-01"
            }
        }

        # Create a note
        note_response = await async_client.post(
            f"/api/calendar/meetings/{meeting.id}/notes",
            json=note_data
        )
        note_id = note_response.json()["id"]

        # Lock meeting
        await async_client.post(f"/api/calendar/meetings/{meeting.id}/lock")

        edited_note_data = {
            "type": MeetingNoteType.RECOMMENDATION.value,
            "form_name": "decision_to_treat",
            "content": {
                "decision": "don't start chemo",
                "date": "2025-08-03"
            }
        }

        # Try editing note
        edit_response = await async_client.put(
            f"/api/calendar/meetings/{meeting.id}/notes/{note_id}",
            json=edited_note_data
        )

        if edit_response.status_code != 403:
            print("Response JSON:", edit_response.json())

        assert edit_response.status_code == 403
    finally:
        app.dependency_overrides.clear()
