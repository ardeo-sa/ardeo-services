from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.database.services import Base


class ClinicalReport(Base):
    __tablename__ = "clinical_reports"

    id = Column(Integer, primary_key=True)
    report_type = Column(String, nullable=False)
    uploaded_at = Column(DateTime, nullable=True)

    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notified = Column(Boolean, default=False)
