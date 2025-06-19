"""Sync google calendar"""
from datetime import datetime, timezone
import httpx


async def push_to_google_calendar(token_data: dict, meeting: dict):
    """
        Asynchronously pushes a meeting to the user's Google Calendar.

        Uses the provided OAuth 2.0 access token and meeting data to create
        a new event in the user's primary Google Calendar via the Google Calendar API.

        Args:
            token_data (dict): A dictionary containing the user's OAuth tokens,
                               must include 'access_token'.
            meeting (dict): A dictionary containing meeting details. Expected keys:
                            'title', 'start_time', 'end_time', and optionally 'description'.

        Returns:
            str: The ID of the created Google Calendar event.

        Raises:
            requests.exceptions.HTTPError: If the API call fails.
    """
    access_token = token_data["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    event_payload = {
        "summary": meeting["title"],
        "start": {"dateTime": meeting["start_time"], "timeZone": "UTC"},
        "end": {"dateTime": meeting["end_time"], "timeZone": "UTC"},
        "description": meeting.get("description", "Scheduled via MDT system"),
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers=headers,
        json=event_payload,
    )
    response.raise_for_status()
    return response.json()["id"]


async def fetch_google_events(token_data: dict, max_results: int = 10) -> list:
    """
    Asynchronously fetches upcoming events from the user's Google Calendar.

    Args:
        token_data (dict): OAuth token data containing at least 'access_token'.
        max_results (int): Maximum number of events to retrieve.

    Returns:
        list: A list of Google Calendar event dictionaries.

    Raises:
        httpx.HTTPStatusError: If the API call fails.
    """
    access_token = token_data["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    now_utc = datetime.now(timezone.utc).isoformat()

    params = {
        "timeMin": now_utc,
        "maxResults": max_results,
        "singleEvents": "true",
        "orderBy": "startTime",
    }

    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            url,
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json().get("items", [])
