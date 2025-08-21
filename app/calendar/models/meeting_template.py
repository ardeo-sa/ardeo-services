"""
SQLAlchemy model for meeting templates.

A meeting template defines reusable configurations for MDT meetings,
including hospital, speciality, location, form references, and team setup.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship

from app.database.services import Base
from app.calendar.enums import TreatmentDecision


class MeetingTemplate(Base):
    """
    Represents a reusable template for creating MDT meetings.

    Attributes:
        speciality (str): The medical speciality of the template (e.g., Oncology).
        hospital (str): The hospital associated with the template.
        location (str): The meeting's location (optional).
        summary_id (str): Foreign key reference to a summary record.
        notes_form_afo_id (str): Foreign key reference to an AF object form.
        treatment_decision (TreatmentDecision): Controlled vocabulary for treatment decisions.
        virtual_meeting (bool): Indicates if the meeting is virtual.
        team (JSON): JSON list of user-role mappings.
        meetings (relationship): Relationship to Meeting objects created from this template.
    """
    __tablename__ = "meeting_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    speciality = Column(String, nullable=False)
    hospital = Column(String, nullable=False)
    location = Column(String, nullable=True)

    summary_id = Column(String, ForeignKey("summary.id"), nullable=True)
    notes_form_afo_id = Column(String, ForeignKey("af_object.afo_id"), nullable=True)

    treatment_decision = Column(Enum(TreatmentDecision), nullable=True)

    virtual_meeting = Column(Boolean, default=False)
    team = Column(JSON, nullable=True)

    meetings = relationship("Meeting", backref="template", lazy="dynamic")

    def __repr__(self) -> str:
        """
        Returns a string representation of the meeting template.

        Returns:
            str: A formatted string containing the template id, speciality, and hospital.
        """
        return f"<MeetingTemplate(id={self.id}, speciality={self.speciality}, hospital={self.hospital})>"
