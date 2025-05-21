"""
Entry point of the FastAPI application.
Initializes the app and includes all routers.
"""
from fastapi import FastAPI
from app.api.router import router as api_router

app = FastAPI(title="Services Management App")

app.include_router(api_router)
