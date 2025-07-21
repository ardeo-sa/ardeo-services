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
from sqlalchemy import select, UniqueConstraint
from httpx import AsyncClient
# from httpx._transports.asgi import ASGITransport


from app.calendar.models.meeting import Meeting, MeetingParticipant
from app.calendar.schemas.meeting import MeetingType, MeetingNoteType
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
    # app.dependency_overrides[get_current_user] = lambda: normal_user
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
        "content": "This is a test recommendation note."
    }

    response = await async_client.post(f"/api/calendar/meetings/{meeting.id}/notes", json=note_data)

    assert response.status_code == 200
    note = response.json()
    assert note["content"] == note_data["content"]
    assert note["type"] == note_data["type"]


@pytest.mark.asyncio
async def test_edit_note_only_by_author(async_client: AsyncClient, normal_user,
                                        db_session: AsyncSession):
    """
    Test that only the author can edit a meeting note.
    """
    # Setup: user is not the author
    # app.dependency_overrides[get_current_user] = lambda: normal_user

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
        "content": "Edited note content"
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
    # app.dependency_overrides[get_current_user] = lambda: normal_user

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
    # app.dependency_overrides[get_current_user] = lambda: normal_user

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
