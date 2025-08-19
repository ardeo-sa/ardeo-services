"""
Entry point of the FastAPI application.
Initializes the app and includes all routers.
"""
import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router import router as api_router
from app.calendar.api.router import router as meetings_router
from app.logging_config import setup_logging

setup_logging()


app = FastAPI(title="Services Management App")

app.include_router(api_router)
app.include_router(meetings_router)

logger = logging.getLogger(__name__)
Instrumentator().instrument(app).expose(app)

@app.get("/health")
def health():
    """App health check"""
    logger.info("Health endpoint called")
    return {"status": "ok"}
