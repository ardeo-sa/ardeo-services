"""
Enums classes used in Pydantic schemas and SQLAlchemy models.

These enums ensure consistent allowed values across both
the database layer (SQLAlchemy) and the API layer (Pydantic).
"""

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


class TreatmentDecision(str, Enum):
    """
    Enum representing the allowed treatment decision values
    in meeting templates.

    Options:
    - `date`
    - `history`
    - `scans`
    - `reason for discussion`
    - `outcome/actions`
    - `primary diagnosis`
    - `referral`
    - `form completed by`
    - `key worker`
    - `attach file`
    - `referred from`
    """
    DATE = "date"
    HISTORY = "history"
    SCANS = "scans"
    REASON_FOR_DISCUSSION = "reason for discussion"
    OUTCOME_ACTIONS = "outcome/actions"
    PRIMARY_DIAGNOSIS = "primary diagnosis"
    REFERRAL = "referral"
    FORM_COMPLETED_BY = "form completed by"
    KEY_WORKER = "key worker"
    ATTACH_FILE = "attach file"
    REFERRED_FROM = "referred from"
