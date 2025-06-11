"""
Calendar synchronization module for external providers (Google and Microsoft).

Provides utilities to fetch and push calendar events between the local system and
external calendar services (Google Calendar, Microsoft Outlook Calendar) using
OAuth tokens stored in the database.
"""
from datetime import datetime

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.calendar.models.oauth import CalendarOAuthToken
from app.users.models.user import User
from app.calendar.models.meeting import Meeting, MeetingType
from app.calendar.services.providers import google, microsoft

def fetch_google_events(token_data: dict):
    """
        Fetches upcoming events from the user's Google Calendar.

        Uses the provided OAuth token to authenticate with the Google Calendar API
        and retrieve the next 10 upcoming events.

        Args:
            token_data (dict): Dictionary containing the user's OAuth tokens, must include 'access_token'.

        Returns:
            list: A list of event dictionaries returned by the Google Calendar API.
    """
    credentials = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/calendar.events"],
    )
    service = build("calendar", "v3", credentials=credentials)

    now = datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(
        calendarId="primary", timeMin=now,
        maxResults=10, singleEvents=True,
        orderBy="startTime"
    ).execute()

    return events_result.get("items", [])


def fetch_microsoft_events(token_data: dict):
    """
        Fetches upcoming events from the user's Microsoft Outlook Calendar.

        Uses Microsoft Graph API to retrieve calendar events starting from the current time
        until a fixed future date.

        Args:
            token_data (dict): Dictionary containing the user's OAuth tokens, must include 'access_token'.

        Returns:
            list: A list of event dictionaries returned by the Microsoft Graph API.

        Raises:
            Exception: If the API request fails.
    """
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}",
        "Content-Type": "application/json"
    }

    now = datetime.utcnow().isoformat() + "Z"
    url = f"https://graph.microsoft.com/v1.0/me/calendarview?startDateTime={now}&endDateTime=2100-01-01T00:00:00Z"

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception("Failed to fetch Microsoft events")

    return response.json().get("value", [])


def sync_user_calendar(user: User, db: Session):
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
    token_record = (
        db.query(CalendarOAuthToken)
        .filter(CalendarOAuthToken.user_id == user.id)
        .first()
    )
    if not token_record:
        raise ValueError("No calendar integration found for this user")

    provider = token_record.provider
    token_data = token_record.token_data

    events = []
    if provider == "google":
        events = fetch_google_events(token_data)
    elif provider == "microsoft":
        events = fetch_microsoft_events(token_data)

    synced_meetings = []
    for event in events:
        meeting = _create_meeting_from_event(db, user, event, provider)
        if meeting:
            synced_meetings.append(meeting)

    db.commit()
    return [m.title for m in synced_meetings]


def _create_meeting_from_event(db: Session, user: User, event: dict, provider: str):
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
    existing = (
        db.query(Meeting)
        .filter_by(external_event_id=external_id, external_provider=provider)
        .first()
    )
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


def push_meeting_to_external(meeting_id: int, user: User, db: Session):
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
    meeting = db.query(Meeting).filter_by(id=meeting_id).first()
    if not meeting:
        raise ValueError("Meeting not found")

    if meeting.external_event_id:
        return "Already synced."

    token = (
        db.query(CalendarOAuthToken)
        .filter_by(user_id=user.id)
        .first()
    )
    if not token:
        raise ValueError("No calendar token found")

    meeting_payload = {
        "title": meeting.title,
        "start_time": meeting.start_time.isoformat(),
        "end_time": meeting.end_time.isoformat(),
        "description": meeting.notes[0].content if meeting.notes else None,
    }

    if token.provider == "google":
        event_id = google.push_to_google_calendar(token.token_data, meeting_payload)
    elif token.provider == "microsoft":
        event_id = microsoft.push_to_outlook_calendar(token.token_data, meeting_payload)
    else:
        raise ValueError("Unsupported provider")

    # Save external reference
    meeting.external_event_id = event_id
    meeting.external_provider = token.provider
    db.commit()
    return f"Pushed to {token.provider} calendar as event ID: {event_id}"
