"""Sync google calendar"""
import requests

def push_to_google_calendar(token_data: dict, meeting: dict):
    """
        Pushes a meeting to the user's Google Calendar.

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

    response = requests.post(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers=headers,
        json=event_payload,
    )
    response.raise_for_status()
    return response.json()["id"]
