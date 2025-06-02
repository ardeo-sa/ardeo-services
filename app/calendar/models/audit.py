from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.services import Base

class MeetingAuditLog(Base):
    __tablename__ = "meeting_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g., add_note, edit_note, upload_file
    object_type = Column(String, nullable=False)  # e.g., note, file, meeting
    object_id = Column(Integer, nullable=True)
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    meeting = relationship("Meeting")
