"""
SQLAlchemy model for the `Patient` entity.

This model represents a patient in the healthcare system who may be involved
in one or more clinical meetings (e.g., MDTs). It includes identifying info,
contact details, and a link to their primary clinician.
"""
import enum

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from app.database.services import Base
from app.users.models.user import User


class Gender(str, enum.Enum):
    """
    Gender definitions
    """
    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"


class Patient(Base):
    """
    SQLAlchemy model representing a patient.
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(SQLAlchemyEnum(Gender), nullable=True)
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
        return f"<Patient(id={self.id}, name='{self.first_name} {self.last_name}')>"
