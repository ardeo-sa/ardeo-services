"""
Calendar synchronization module for external providers (Google and Microsoft).

Provides utilities to fetch and push calendar events between the local system and
external calendar services (Google Calendar, Microsoft Outlook Calendar) using
OAuth tokens stored in the database.
"""
from datetime import datetime, timezone
import os
import asyncio
from functools import partial

import httpx
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.calendar.models.oauth import CalendarOAuthToken
from app.users.models.user import User
from app.calendar.models.meeting import Meeting, MeetingType
from app.calendar.services.providers import google, microsoft

async def fetch_google_events(token_data: dict):
    """
    Fetches upcoming events from the user's Google Calendar asynchronously.

    Args:
        token_data (dict): OAuth token data with 'access_token'.

    Returns:
        list: A list of Google Calendar event dictionaries.
    """
    credentials = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/calendar.events"],
    )

    # This is a blocking call, so we'll run it in a thread
    service = await asyncio.to_thread(build, "calendar", "v3", credentials=credentials)

    now = datetime.now(timezone.utc).isoformat()
    request: HttpRequest = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy="startTime"
    )

    # The request execution is blocking; run it in a thread too
    events_result = await asyncio.to_thread(request.execute)

    return events_result.get("items", [])


async def fetch_microsoft_events(token_data: dict):
    """
    Fetches upcoming events from the user's Microsoft Outlook Calendar asynchronously.

    Uses Microsoft Graph API to retrieve calendar events from now until a fixed future date.

    Args:
        token_data (dict): OAuth token data with 'access_token'.

    Returns:
        list: A list of Microsoft Graph event dictionaries.

    Raises:
        Exception: If the API request fails.
    """
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}",
        "Content-Type": "application/json"
    }

    now = datetime.now(timezone.utc).isoformat()
    url = (
        "https://graph.microsoft.com/v1.0/me/calendarview"
        f"?startDateTime={now}&endDateTime=2100-01-01T00:00:00Z"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch Microsoft events: {response.text}")

    return response.json().get("value", [])


async def sync_user_calendar(user: User, db: AsyncSession):
    """
        Syncs events from the user's external calendar into the local database.

        Determines the provider (Google or Microsoft), fetches events from their calendar,
        and creates corresponding `Meeting` entries locally if they haven't already been synced.

        Args:
            user (User): The user whose calendar should be synced.
            db (Session): SQLAlchemy session for database operations.

        Returns:
            list: Titles of the synced meetings.

        Raises:
            ValueError: If the user has no linked calendar token.
    """
    token_record = await db.execute(
        select(CalendarOAuthToken).where(CalendarOAuthToken.user_id == user.id)
    )
    token_record = token_record.scalar_one_or_none()
    if not token_record:
        raise ValueError("No calendar integration found for this user")

    provider = token_record.provider
    token_data = token_record.token_data

    events = []
    if provider == "google":
        events = await fetch_google_events(token_data)
    elif provider == "microsoft":
        events = await fetch_microsoft_events(token_data)

    synced_meetings = []
    for event in events:
        meeting = _create_meeting_from_event(db, user, event, provider)
        if meeting:
            synced_meetings.append(meeting)

    await db.commit()
    return [m.title for m in synced_meetings]


async def _create_meeting_from_event(db: AsyncSession, user: User, event: dict, provider: str):
    """
       Converts an external calendar event into a local Meeting record.

       Ensures duplicates aren't created by checking for an existing external_event_id.

       Args:
           db (Session): SQLAlchemy session for database operations.
           user (User): The user syncing the event.
           event (dict): Dictionary containing event data from the provider.
           provider (str): The name of the calendar provider ('google' or 'microsoft').

       Returns:
           Meeting or None: The new Meeting object if created, otherwise None.
    """
    external_id = event["id"]
    title = event.get("summary") or event.get("subject", "Untitled")
    start_str = event["start"].get("dateTime") or event["start"].get("date")
    end_str = event["end"].get("dateTime") or event["end"].get("date")

    # Parse datetimes
    start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))

    # Check if already synced
    stmt = select(Meeting).filter_by(external_event_id=external_id, external_provider=provider)
    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing:
        return None  # Skip duplicates

    meeting = Meeting(
        title=title,
        start_time=start,
        end_time=end,
        type=MeetingType.regular,  # External events are not MDTs
        created_by_id=user.id,
        external_event_id=external_id,
        external_provider=provider,
    )
    db.add(meeting)
    return meeting


async def push_meeting_to_external(meeting_id: int, user: User, db: AsyncSession):
    """
        Pushes a local meeting to the user's external calendar (Google or Microsoft).

        Converts the local meeting object into the provider's expected format and uses
        the appropriate API to create the event. Saves the external event ID after pushing.

        Args:
            meeting_id (int): ID of the meeting to push.
            user (User): The user whose calendar will receive the event.
            db (Session): SQLAlchemy session for database access.

        Returns:
            str: Confirmation message with the external event ID.

        Raises:
            ValueError: If the meeting or calendar token is not found, or provider is unsupported.
    """
    # meeting = db.query(Meeting).filter_by(id=meeting_id).first()
    stmt = select(Meeting).filter_by(id=meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalars().first()
    if not meeting:
        raise ValueError("Meeting not found")

    if meeting.external_event_id:
        return "Already synced."

    # token = (
    #     db.query(CalendarOAuthToken)
    #     .filter_by(user_id=user.id)
    #     .first()
    # )
    stmt = select(CalendarOAuthToken).filter_by(user_id=user.id)
    result = await db.execute(stmt)
    token = result.scalars().first()

    if not token:
        raise ValueError("No calendar token found")

    meeting_payload = {
        "title": meeting.title,
        "start_time": meeting.start_time.isoformat(),
        "end_time": meeting.end_time.isoformat(),
        "description": meeting.notes[0].content if meeting.notes else None,
    }

    if token.provider == "google":
        event_id = await asyncio.to_thread(google.push_to_google_calendar, token.token_data, meeting_payload)
    elif token.provider == "microsoft":
        event_id = await asyncio.to_thread(microsoft.push_to_outlook_calendar, token.token_data, meeting_payload)
    else:
        raise ValueError("Unsupported provider")

    # Save external reference
    meeting.external_event_id = event_id
    meeting.external_provider = token.provider
    await db.commit()
    return f"Pushed to {token.provider} calendar as event ID: {event_id}"
