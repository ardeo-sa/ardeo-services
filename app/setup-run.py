# from app.database import services
from app.database.services import Base, get_services_engine

# from app.calendar.models.audit import MeetingAuditLog
# from app.calendar.models.meeting import Meeting,MeetingNote,MeetingPatient,MeetingParticipant,SupportingFile
# from app.patients.models.patient import Patient
# from app.users.models.user import User
# from app.messaging.models.messaging import Message,Conversation
# from app.calendar.models.oauth import CalendarOAuthToken

services_engine = get_services_engine()
Base.metadata.create_all(services_engine)
