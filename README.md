# Services Management Backend (FastAPI)

This is a FastAPI-based backend service for Ardeo web application. It provides functionality for:

- Scheduling and managing regular meetings and MDT (Multidisciplinary Team) meetings
- Associating subjects and participants with meetings
- Capturing structured notes during MDT meetings (discussion, recommendations, conclusions)
- Ensuring proper access control (in progress)
- Persisting all meeting data for future browsing and auditing
- Swagger/OpenAPI integration for API testing

## Current API Features

### Create a Meeting

**Endpoint:** `POST /calendar/meetings/`  
**Description:** Creates a new meeting of type `regular` or `mdt`.  

**Payload Example:**
```json
{
  "title": "MDT Weekly",
  "start_time": "2025-05-22T09:00:00",
  "end_time": "2025-05-22T10:00:00",
  "type": "mdt",
  "participants": [1, 2, 3],
  "patient_ids": [101, 102]
}
```

### Get a Meeting
**Endpoint:** `GET /calendar/meetings/{meeting_id}`
**Description:** Retrieves full meeting details, including participants, notes, and lock status

### Notes on MDT Meetings
- Only MDT meetings allow patient associations and special note-taking.
- Meeting content can be locked to prevent post-meeting edits.
- Notes are structured by type: discussion, recommendation, conclusion, etc.

## Tech Stack
- FastAPI – modern Python web framework
- Pydantic – request/response schema validation
- SQLAlchemy – ORM and DB model management
- Postgres - data recorded in a service data base
- Uvicorn – ASGI server for development


## Project Structure

- `app/` - Main application code
  - `core/` - Common utilities and config (e.g., DB, auth)
  - `calendar/` - All calendar, meeting, and sync logic
  - `users/` - User management
  - `patients/` - Patient data models and logic
  - `api/` - Route entry points
- `tests/` - Unit and integration tests

### Notes
- Google/Outlook sync is handled in `calendar/services/`
- Background jobs (e.g. reminders) go in `calendar/tasks/`


## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the FastAPI app:
```bash
uvicorn app.main:app --reload
```

3. Running Tests
```bash
pytest tests/
```


## API Documentation
The FastAPI backend provides automatic, interactive API documentation using the OpenAPI standard. 
This makes it easy to test endpoints, understand expected payloads, and share the API with third-party 
integrators or frontend developers.

### Interactive Docs
Once the application is running, you can explore and test all available API endpoints through the 
following built-in UIs:

- Swagger UI:
http://localhost:8000/docs – Interactive documentation with support for live requests and token-based authentication.

- ReDoc:
http://localhost:8000/redoc – Clean, read-only reference-style documentation.

These UIs are automatically generated from your FastAPI routes, response_models, and Pydantic schemas.

### Customizing Docs
- Tags: Routes are grouped by tags like Meetings, Users, or Patients to improve organization.
- Descriptions: You can define endpoint-level and tag-level descriptions to clarify business logic.
- Schema Examples: Pydantic models include examples for request and response payloads.
- Metadata: You can set custom project-level metadata like title, version, and contact info in FastAPI()

```python
app = FastAPI(
    title="Ardeo Services API",
    version="1.0.0",
    description="Backend for meeting scheduling, MDT workflow, and patient management."
)
```
