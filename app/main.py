"""
Entry point of the FastAPI application.
Initializes the app and includes all routers.
"""
from fastapi import FastAPI
from app.api.router import router as api_router

from  app.calendar.api.router import router as meetings_router
# from app.database import services
from app.database.services import Base, get_services_engine

app = FastAPI(title="Services Management App")
# to create tables in db run below
# from app.calendar.models.audit import MeetingAuditLog
# from app.calendar.models.meeting import Meeting,MeetingNote,MeetingPatient,MeetingParticipant,SupportingFile
# from app.patients.models.patient import Patient
# from app.users.models.user import User
# from app.messaging.models.messaging import Message,Conversation
# from app.calendar.models.oauth import CalendarOAuthToken
#
# services_engine = get_services_engine()
# Base.metadata.create_all(services_engine)

app.include_router(api_router)
app.include_router(meetings_router)
