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


## Manual Setup (dev)
1. Create & activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables
Copy .env.example (if present) to .env and update values as needed (DB connection string, secrets, etc.).

4. Ensure required services are running (e.g., Redis, PostgreSQL)
Start Redis (use instructions above to enable it)

5. Run the FastAPI app:
```bash
python run.py
```
6. Run background metrics aggregation
```bash
# Run celery
celery -A app.tasks.worker worker --beat --loglevel=info
```

7. Monitor celery tasks
```bash
# Use flower dashboard to monitor 
# http://localhost:5555
celery -A app.tasks.worker flower --port=5555
```

### To run in prod as service
```bash
# 1. Create dedicated user
sudo useradd -r -s /bin/false dash-runner

2. copy config
sudo cp ardeo-dash.service /etc/systemd/system/

# 3. enable and start
sudo systemctl daemon-reload
sudo systemctl enable ardeo-dash.service
sudo systemctl start ardeo-dash.service

# 3. Check logs
journalctl -u ardeo-dash.service -f 
```

### Docker
```bash
# Run all services
docker compose up -d
```

## Optional setup steps
### Install Redis server
#### Manual Setup (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Redis
sudo apt install redis-server

# Start Redis
sudo systemctl start redis

# (Optional) Enable Redis to start on boot
sudo systemctl enable redis

# Verify it's running
redis-cli ping
```
#### Run docker
```bash
# Pull the latest lightweight Redis image and starts it on port 6379
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine
# Verify
docker logs redis
docker exec -it redis redis-cli ping
```

### Install PostgreSQL
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql

# To enable it at boot
sudo systemctl enable postgresql

# Verify
sudo systemctl status postgresql

# Connect to test
sudo -u postgres psql
# Run
\conninfo
# Quit
\q
```

### Databse setup
```bash
# Run once to create database and users
./utils/setup_services_db.sh
```

## Maintainance
### Reporting database migrations
```bash
# Generate initial migration
alembic revision --autogenerate -m "init reporting models"

# Generate migrations when models change
alembic revision --autogenerate -m "add new table xyz"

# Apply migrations
alembic upgrade head
```

### Troubleshooting
* Connection Refused errors? Make sure Redis, Postgres, or other services your app depends on are running.
* WireGuard traffic not routing correctly? Avoid using the same LAN subnet as the remote peer (e.g., 192.168.0.0/24).
* Can't SSH to internal IPs via VPN? Ensure your local IP doesn't conflict and the server allows forwarding.

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

## API Testing & Coverage
We use pytest with modern async tools and realistic test data generation.

### Tools
pytest – main test runner
pytest-asyncio – async test support
httpx.AsyncClient – for testing FastAPI endpoints
pytest-cov – coverage reporting
factory_boy & Faker – for generating mock users, patients, etc.

### Running Tests
bash
Copy
Edit
pytest --cov=app --cov-report=term-missing

### Example Test
```python
async def test_create_meeting(async_client, override_coord):
    payload = {
        "title": "Weekly MDT",
        "type": "mdt",
        "scheduled_at": "2025-06-10T10:00:00Z"
    }
    response = await async_client.post("/api/meetings/", json=payload)
    assert response.status_code == 200
```

### View HTML Coverage
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```
