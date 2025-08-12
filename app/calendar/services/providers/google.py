"""Sync google calendar"""
import logging
from datetime import datetime, timezone
import httpx

logger = logging.getLogger(__name__)

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

    logger.info("Pushing meeting to Google Calendar")
    logger.debug(f"Event payload: {event_payload}")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers=headers,
                json=event_payload,
            )
            response.raise_for_status()
            event_id = response.json()["id"]
            logger.info(f"Successfully created Google Calendar event: {event_id}")
            return event_id
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create event: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.exception("Unexpected error while pushing to Google Calendar")
            raise


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
    logger.info("Fetching events from Google Calendar")
    logger.debug(f"Request params: {params}")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(
                url,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            items = response.json().get("items", [])
            logger.info(f"Retrieved {len(items)} events from Google Calendar")
            return items
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch events: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.exception("Unexpected error while fetching Google Calendar events")
            raise
