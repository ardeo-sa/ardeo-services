"""
Module for pushing calendar events to Microsoft Outlook Calendar via Microsoft Graph API.

Provides functionality to create events in a user's Outlook calendar using
OAuth 2.0 access tokens and meeting metadata.
"""
import logging
from datetime import datetime, timezone
import httpx

logger = logging.getLogger(__name__)

async def push_to_outlook_calendar(token_data: dict, meeting: dict):
    """
        Pushes a meeting asynchronously to the user's Microsoft Outlook Calendar.

        Uses the provided OAuth 2.0 access token and meeting data to create
        a new event in the user's Outlook calendar via the Microsoft Graph API.

        Args:
            token_data (dict): Dictionary containing OAuth tokens, must include 'access_token'.
            meeting (dict): Dictionary containing meeting details. Expected keys:
                            'title', 'start_time', 'end_time', and optionally 'description'.

        Returns:
            str: The ID of the created Outlook calendar event.

        Raises:
            requests.exceptions.HTTPError: If the API call fails.
    """
    access_token = token_data["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    event_payload = {
        "subject": meeting["title"],
        "start": {
            "dateTime": meeting["start_time"],
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": meeting["end_time"],
            "timeZone": "UTC"
        },
        "body": {
            "contentType": "Text",
            "content": meeting.get("description", "Scheduled via MDT system")
        }
    }

    logger.info("Pushing meeting to Microsoft Outlook Calendar")
    logger.debug(f"Event payload: {event_payload}")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(
                "https://graph.microsoft.com/v1.0/me/events",
                headers=headers,
                json=event_payload,
            )
            response.raise_for_status()
            event_id = response.json()["id"]
            logger.info(f"Successfully created Outlook event: {event_id}")
            return event_id
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create Outlook event: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.exception("Unexpected error while pushing to Outlook Calendar")
            raise


async def get_outlook_events(token_data: dict):
    """
    Fetches upcoming events from the user's Microsoft Outlook Calendar via Microsoft Graph API.

    Args:
        token_data (dict): Dictionary containing OAuth tokens, must include 'access_token'.

    Returns:
        list: List of calendar events as dictionaries.

    Raises:
        httpx.HTTPError: If the API call fails.
    """
    access_token = token_data["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    now = datetime.now(timezone.utc).isoformat()
    future = "2100-01-01T00:00:00Z"
    url = (
        f"https://graph.microsoft.com/v1.0/me/calendarview"
        f"?startDateTime={now}&endDateTime={future}"
    )

    logger.info("Fetching events from Microsoft Outlook Calendar")
    logger.debug(f"Request URL: {url}")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            items = response.json().get("value", [])
            logger.info(f"Retrieved {len(items)} events from Outlook Calendar")
            return items
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch Outlook events: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.exception("Unexpected error while fetching Outlook events")
            raise
