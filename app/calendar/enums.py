"""Enums classes used in pydantic schemas and SQLAlchemy models"""
from enum import Enum

class MeetingType(str, Enum):
    """
        Enum representing the type of meeting.

        Options:
        - `regular`: A standard meeting with general discussions.
        - `mdt`: A multidisciplinary team (MDT) meeting involving collaborative decision-making across specialties.
    """
    REGULAR = "regular"
    MDT = "mdt"


class MeetingNoteType(str, Enum):
    """
        Enum representing the type of note taken during a meeting.

        Options:
        - `discussion`: General discussion points.
        - `recommendation`: Suggestions or advice based on discussion.
        - `conclusion`: Final decisions or outcomes from the meeting.
    """
    DISCUSSION = "discussion"
    RECOMMENDATION = "recommendation"
    CONCLUSION = "conclusion"
