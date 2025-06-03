import requests

def push_to_google_calendar(token_data: dict, meeting: dict):
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
