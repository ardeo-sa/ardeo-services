# Calendar App Backend

This is the backend service for the calendar and MDT meeting management system.

## Structure

- `app/` - Main application code
  - `core/` - Common utilities and config (e.g., DB, auth)
  - `calendar/` - All calendar, meeting, and sync logic
  - `users/` - User management
  - `patients/` - Patient data models and logic
  - `api/` - Route entry points
- `tests/` - Unit and integration tests

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the FastAPI app:
```bash
uvicorn app.main:app --reload
```

## Notes
- Google/Outlook sync is handled in `calendar/services/`
- Background jobs (e.g. reminders) go in `calendar/tasks/`
