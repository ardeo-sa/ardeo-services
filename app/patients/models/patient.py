"""
SQLAlchemy model for the `Patient` entity.

This model represents a patient in the healthcare system who may be involved
in one or more clinical meetings (e.g., MDTs). It includes identifying info,
contact details, and a link to their primary clinician.
"""
import enum

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum as SQLEnum, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database.services import Base


class Gender(str, enum.Enum):
    """
    Gender definitions
    """
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class Patient(Base):
    """
    SQLAlchemy model representing a patient.
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(SQLEnum(Gender), nullable=True)
    medical_record_number = Column(String, unique=True, nullable=True)

    contact_info = Column(String, nullable=True)
    next_of_kin = Column(String, nullable=True)

    primary_clinician_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    primary_clinician = relationship("User", backref="patients")

    meeting_links = relationship(
        "MeetingPatient",
        back_populates="patient",
        cascade="all, delete-orphan"
    )

    meetings = relationship(
        "Meeting",
        secondary="meeting_patients",
        viewonly=True,
        back_populates="patients"
    )

    def __repr__(self):
        """
           Returns a string representation of the Patient instance for debugging purposes.

           Includes the patient ID and full name.
        """
        return f"<Patient(id={self.id}, name='{self.first_name} {self.last_name}')>"


    @property
    def name(self) -> str:
        """Dynamically combines first_name and last_name every time name is required"""
        return f"{self.first_name} {self.last_name}"


class CareStep(Base):
    """
    Represents an actionable clinical step for a patient (e.g., diagnostic,
    treatment, or follow-up), with due/completion dates.

    Used for care pathway tracking and notification logic.
    """
    __tablename__ = "care_steps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    patient = relationship("Patient", backref="care_steps")

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", backref="owned_care_steps")

    def __repr__(self):
        return f"<CareStep(id={self.id}, name='{self.name}', due_date={self.due_date})>"

