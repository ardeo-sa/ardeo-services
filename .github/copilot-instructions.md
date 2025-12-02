# Ardeo Services - AI Agent Coding Guide

## Architecture Overview

**Ardeo Services** is a FastAPI backend for healthcare meeting management with three core responsibilities:

1. **Calendar & Meetings** (`app/calendar/`): Meeting lifecycle (CRUD), participant management, MDT (multidisciplinary team) workflows, and external calendar sync (Google/Microsoft)
2. **Notifications** (`app/notifications/`): Event-driven notification dispatch via email, WhatsApp, and in-app channels with user preference tracking
3. **Messaging** (`app/messaging/`): Conversation threads for meeting discussions

### Stack
- **Framework**: FastAPI with Pydantic validation
- **Async/ORM**: SQLAlchemy + asyncio + asyncpg (PostgreSQL)
- **Background Jobs**: Celery + Redis (broker & result backend)
- **Testing**: pytest-asyncio with async test client (httpx.AsyncClient)

---

## Critical Patterns

### 1. Async/Await with SQLAlchemy
**All database operations use async patterns.** Never use sync `Session`; always use `AsyncSession`.

**Key pattern**:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import async_session_maker

async def get_meeting(meeting_id: int, db: AsyncSession):
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    return result.scalar_one_or_none()
```

**Important**:
- Use `await db.execute()` for all queries
- Use `await db.flush()` when inserting/updating before accessing relationships
- Use `await db.commit()` for persistence
- Use `selectinload()` to eagerly load relationships (avoids N+1 queries)

### 2. Dependency Injection & Authentication
All routes receive `db: AsyncSession = Depends(get_services_db)` and `current_user: User = Depends(get_current_user)` via FastAPI dependency injection.

**Example** (`app/calendar/services/meeting.py`):
```python
async def create_meeting(meeting_data: MeetingCreate, db: AsyncSession, current_user: User):
    new_meeting = Meeting(
        title=meeting_data.title,
        created_by=current_user.id,  # Track creator
        ...
    )
    db.add(new_meeting)
    await db.flush()
    # Add relationships, then commit
    await db.commit()
    return new_meeting
```

**Auth flow**:
- `get_current_user()` retrieves from `request.state.user` (set by upstream auth middleware)
- `require_role("coordinator")` factory checks role before allowing action
- Access control is **not yet fully enforced** across all endpoints (flagged in README)

### 3. Meeting Model Relationships
Meetings have complex multi-table relationships. Always use appropriate eager loading:

```python
# In services: use selectinload for N+1 prevention
result = await db.execute(
    select(Meeting)
    .options(selectinload(Meeting.participants), 
             selectinload(Meeting.notes))
    .where(Meeting.id == meeting_id)
)

# In schemas: transform ORM objects to Pydantic
class MeetingDetail(BaseModel):
    id: int
    title: str
    participants: List[UserOut]
    notes: List[MeetingNoteResponse]
```

**Key models** (`app/calendar/models/meeting.py`):
- `Meeting`: Has participants (M2M via `MeetingParticipant`), notes, patients (MDT only)
- `MeetingParticipant`: Junction table linking users to meetings
- `MeetingNote`: Typed notes (discussion/recommendation/conclusion) with JSON content
- `MeetingPatient`: Junction table for MDT patient associations

### 4. Notification Dispatch Pattern
Notifications are **event-driven** and routed through user preferences. The service checks delivery methods (email, WhatsApp, in-app) and delegates to channel-specific utilities.

**Flow** (`app/notifications/services.py`):
```python
async def send_notification(self, notif: Notification):
    pref = await get_user_preferences(self.db, notif.user_id)
    methods = pref.delivery_methods if pref else ["in_app"]  # Default fallback
    
    for method in methods:
        if method == "email":
            await send_email_notification(notif)
        elif method == "whatsapp":
            await send_whatsapp_message(notif)
```

**Trigger system**: `app/notifications/triggers.py` defines what events should generate notifications. Use condition operators like `within_hours`, `>=`, `==` on watched items.

### 5. Celery Background Tasks
Periodic and event-triggered tasks run via Celery. **Always wrap async code** in `asyncio.run()` inside sync Celery tasks.

**Pattern** (`app/tasks/celery_notification_tasks.py`):
```python
@celery_app.task
def run_system_notifications():
    async def _run():
        async with async_session_maker() as session:
            await generate_system_notifications(session)
    
    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        raise
```

**Schedule** (in `app/celery_app.py`):
- `run_system_notifications`: Every 5 minutes
- `sync_all_user_calendars`: Every 30 minutes

Monitor via Flower: `celery -A app.celery_app.celery_app flower --port=5555`

---

## Testing Conventions

### Fixtures
All fixtures are in `tests/fixtures/` and auto-registered in `tests/conftest.py`:
- `db_session`: In-memory async SQLAlchemy session
- `async_client`: httpx.AsyncClient with overridden DB dependency
- `normal_user`, `coordinator_user`: Pre-created User ORM objects
- `meeting_data`: Sample MDT meeting payload

### Test Pattern
```python
@pytest.mark.asyncio
async def test_create_meeting(async_client, normal_user):
    app.dependency_overrides[get_current_user] = lambda: normal_user
    
    response = await async_client.post("/api/calendar/meetings/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == payload["title"]
```

**Run tests**:
```bash
pytest --cov=app --cov-report=term-missing  # All tests with coverage
pytest tests/test_calendar_meetings.py       # Single file
```

---

## Development Workflows

### Local Setup
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp env-example .env  # Configure DB, Redis, OAuth, SMTP, Twilio
docker compose up -d  # PostgreSQL, Redis, Celery worker/beat
python run.py        # Start FastAPI at http://localhost:8000
```

### Schema & Validation
- All endpoint inputs use Pydantic schemas (`app/*/schemas/*.py`)
- All responses are typed Pydantic models
- Use `BaseModel.model_dump()` to convert ORM → Pydantic for responses
- FastAPI automatically generates OpenAPI docs at `/docs`

### Environment Variables
- **Database**: `SERVICES_DB_USER`, `SERVICES_DB_PASSWORD`, `SERVICES_DB_HOST`, `SERVICES_DB_PORT`, `SERVICES_DB_NAME` (or `SERVICES_DB_URI`)
- **Redis**: `REDIS_URL` (default: `redis://localhost:6379/0`)
- **OAuth**: `GOOGLE_CLIENT_ID`, `MICROSOFT_CLIENT_ID`, etc.
- **Notifications**: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `TWILIO_ACCOUNT_SID`, etc.

### Database Migrations
Use Alembic for schema changes:
```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head  # Apply migrations
```

---

## Key File Reference

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app initialization, router includes, health check |
| `app/config.py` | Environment variable loading, DB URI construction |
| `app/database/session.py` | Async SQLAlchemy engine & session factory |
| `app/core/dependencies.py` | Auth dependencies (`get_current_user`, `require_role`) |
| `app/calendar/services/meeting.py` | Meeting creation, validation, participant/note logic |
| `app/notifications/services.py` | Notification creation & dispatch dispatcher |
| `app/notifications/utils/delivery.py` | Channel-specific sending (email, WhatsApp) |
| `app/celery_app.py` | Celery config, beat schedule definition |
| `tests/conftest.py` | Pytest fixture registration & event loop setup |
| `docker-compose.yml` | Services: web, celery_worker, celery_beat, postgres, redis |

---

## Common Pitfalls to Avoid

1. **Forgetting `await`** on async DB calls → Runtime errors
2. **Using sync `Session` instead of `AsyncSession`** → Type mismatch
3. **Missing `selectinload()` for relationships** → N+1 query explosions
4. **Not calling `await db.flush()` before accessing new IDs** → AttributeError on related objects
5. **Auth middleware not setting `request.state.user`** → 401 errors in all routes
6. **Celery tasks not wrapping async code in `asyncio.run()`** → Undefined event loop errors
7. **Test fixtures not using `db_session` dependency** → Real DB queries in tests instead of in-memory

---

## Integration Points

- **Google/Microsoft Calendar Sync**: `app/calendar/services/providers/google.py`, `microsoft.py` – OAuth flow, event pull/push
- **Notifications**: Triggered by meeting changes, user actions → routed via `NotificationService`
- **Messaging**: Separate conversation threads per meeting, integrates with notifications for new messages
- **Audit**: `app/calendar/models/audit.py` tracks changes on sensitive operations (meeting lock, note retraction)

---

## Logging & Debugging

All modules use structured logging with `logging.getLogger(__name__)`:
- **Level**: DEBUG for routine operations, INFO for business events, ERROR/WARNING for issues
- **Context**: Include user_id, meeting_id, operation name in log messages
- **Format**: Configured in `app/logging_config.py` with JSON support for production

Example:
```python
logger.info(f"Meeting created: meeting_id={meeting.id}, created_by={current_user.id}")
```

---

## Health Checks & Monitoring

- **App Health**: `GET /health` → `{"status": "ok"}`
- **Prometheus Metrics**: Auto-instrumented via `prometheus-fastapi-instrumentator`
- **Celery Tasks**: Monitor via Flower dashboard (see Celery section above)
- **Logs**: Check container logs or `app.log`, `celery_worker.log`, `celery_beat.log` files
