"""
Module for pushing calendar events to Microsoft Outlook Calendar via Microsoft Graph API.

Provides functionality to create events in a user's Outlook calendar using
OAuth 2.0 access tokens and meeting metadata.
"""
import requests

def push_to_outlook_calendar(token_data: dict, meeting: dict):
    """
        Pushes a meeting to the user's Microsoft Outlook Calendar.

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

    response = requests.post(
        "https://graph.microsoft.com/v1.0/me/events",
        headers=headers,
        json=event_payload,
    )
    response.raise_for_status()
    return response.json()["id"]
