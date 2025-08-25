"""
Database setup module.

This module initializes the database schema by creating all tables
defined in the application's SQLAlchemy models. No data migration or
modification is performed—only table creation if missing.

Usage:
    Simply import this module to ensure all tables exist.
"""
# pylint: disable=unused-import
import logging
from app.database.services import Base, get_services_engine

# Import all models to register them with Base.metadata
from app.calendar.models.audit import MeetingAuditLog
from app.calendar.models.meeting import Meeting, MeetingNote, MeetingPatient, MeetingParticipant, SupportingFile
from app.patients.models.patient import Patient
from app.users.models.user import User
from app.messaging.models.messaging import Message, Conversation
from app.calendar.models.oauth import CalendarOAuthToken

logger = logging.getLogger(__name__)

# Initialize the database engine
services_engine = get_services_engine()

# Create all tables registered in Base.metadata
Base.metadata.create_all(services_engine)

logger.info("Database tables have been created (if they did not exist).")
