import requests

def push_to_outlook_calendar(token_data: dict, meeting: dict):
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
