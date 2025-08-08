"""
Calendar synchronization module for external providers (Google and Microsoft).

Provides utilities to fetch and push calendar events between the local system and
external calendar services (Google Calendar, Microsoft Outlook Calendar) using
OAuth tokens stored in the database.
"""
import logging
from datetime import datetime, timezone
import os
import asyncio

import httpx
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.calendar.models.oauth import CalendarOAuthToken
from app.users.models.user import User
from app.calendar.models.meeting import Meeting, MeetingType
from app.calendar.services.providers import google, microsoft

logger = logging.getLogger(__name__)

async def fetch_google_events(token_data: dict):
    """
    Fetches upcoming events from the user's Google Calendar asynchronously.

    Args:
        token_data (dict): OAuth token data with 'access_token'.

    Returns:
        list: A list of Google Calendar event dictionaries.
    """
    logger.info("Fetching Google Calendar events...")
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
    events = events_result.get("items", [])

    logger.info(f"Fetched {len(events)} events from Google Calendar.")
    return events


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
    logger.info("Fetching Microsoft Calendar events...")
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
        logger.error(f"Microsoft Calendar API failed: {response.text}")
        raise HTTPException(status_code=response.status_code, detail=f"Microsoft Calendar API failed {response.text}")

    events = response.json().get("value", [])
    logger.info(f"Fetched {len(events)} events from Microsoft Calendar.")
    return events


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
    logger.info(f"Starting calendar sync for user {user.id} ({user.email})...")
    token_record = await db.execute(
        select(CalendarOAuthToken).where(CalendarOAuthToken.user_id == user.id)
    )
    token_record = token_record.scalar_one_or_none()
    if not token_record:
        logger.warning("No calendar integration found for this user.")
        raise ValueError("No calendar integration found for this user")

    provider = token_record.provider
    token_data = token_record.token_data
    logger.info(f"Detected provider: {provider}")

    events = []
    if provider == "google":
        events = await fetch_google_events(token_data)
    elif provider == "microsoft":
        events = await fetch_microsoft_events(token_data)
    else:
        logger.error(f"Unsupported provider: {provider}")
        raise ValueError("Unsupported provider")

    synced_meetings = []
    for event in events:
        meeting = await _create_meeting_from_event(db, user, event, provider)
        if meeting:
            logger.info(f"Created meeting '{meeting.title}' from {provider} event.")
            synced_meetings.append(meeting)
        else:
            logger.debug(f"Skipped duplicate event from {provider}: {event.get('id')}")

    await db.commit()
    logger.info(f"Calendar sync complete. {len(synced_meetings)} new meetings added.")
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
    logger.info(f"Starting meeting creation {event.id} ...")
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
        logger.debug(f"Meeting already exists for event {external_id}. Skipping.")
        return None

    meeting = Meeting(
        title=title,
        start_time=start,
        end_time=end,
        type=MeetingType.REGULAR,  # External events are not MDTs
        created_by_id=user.id,
        external_event_id=external_id,
        external_provider=provider,
    )
    db.add(meeting)
    logger.debug(f"Prepared meeting object for event {external_id}.")
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
    logger.info(f"Pushing meeting {meeting_id} to external calendar for user {user.id}...")

    stmt = select(Meeting).filter_by(id=meeting_id)
    result = await db.execute(stmt)
    meeting = result.scalars().first()
    if not meeting:
        logger.error("Meeting not found.")
        raise ValueError("Meeting not found")

    if meeting.external_event_id:
        logger.info(f"Meeting {meeting_id} already synced as event {meeting.external_event_id}.")
        return "Already synced."

    stmt = select(CalendarOAuthToken).filter_by(user_id=user.id)
    result = await db.execute(stmt)
    token = result.scalars().first()

    if not token:
        logger.error("No calendar token found.")
        raise ValueError("No calendar token found")

    meeting_payload = {
        "title": meeting.title,
        "start_time": meeting.start_time.isoformat(),
        "end_time": meeting.end_time.isoformat(),
        "description": meeting.notes[0].content if meeting.notes else None,
    }
    logger.debug(f"Prepared payload for push: {meeting_payload}")

    if token.provider == "google":
        event_id = await asyncio.to_thread(google.push_to_google_calendar, token.token_data, meeting_payload)
    elif token.provider == "microsoft":
        event_id = await asyncio.to_thread(microsoft.push_to_outlook_calendar, token.token_data, meeting_payload)
    else:
        logger.error(f"Unsupported provider: {token.provider}")
        raise ValueError("Unsupported provider")

    # Save external reference
    meeting.external_event_id = event_id
    meeting.external_provider = token.provider
    await db.commit()
    logger.info(f"Successfully pushed meeting {meeting_id} to {token.provider} as event {event_id}.")
    return f"Pushed to {token.provider} calendar as event ID: {event_id}"
