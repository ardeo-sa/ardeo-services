"""
Tests for calendar-related endpoints using template fixtures.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_meetings(mock_meeting, override_current_user_coord, async_client: AsyncClient):
    """
    Test fetching meetings for a coordinator user.
    """
    response = await async_client.get("/calendar/meetings")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(meeting["id"] == str(mock_meeting.id) for meeting in data)


@pytest.mark.asyncio
async def test_shared_meeting_access(shared_meeting, normal_user, override_current_user_normal, async_client: AsyncClient):
    """
    Test that a normal user can access a shared meeting.
    """
    response = await async_client.get(f"/calendar/meetings/{shared_meeting.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(shared_meeting.id)
    assert "Shared Meeting" in data["title"]


@pytest.mark.asyncio
async def test_meeting_with_participants(meeting_with_participants, override_current_user_coord, async_client: AsyncClient):
    """
    Test that meeting with participants returns the correct participant list.
    """
    response = await async_client.get(f"/calendar/meetings/{meeting_with_participants.id}")
    assert response.status_code == 200
    data = response.json()
    participants_ids = [p["id"] for p in data.get("participants", [])]
    assert all(str(p.id) in participants_ids for p in meeting_with_participants.participants)
