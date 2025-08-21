"""
Business logic for meeting template operations such as creation, update,
retrieval, and deletion.

Meeting templates define reusable configurations for MDT meetings,
including hospital, speciality, location, and team composition.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException

from app.calendar.models.meeting_template import MeetingTemplate
from app.calendar.schemas.meeting_template import (
    MeetingTemplateCreate,
    MeetingTemplateUpdate,
)
from app.users.models.user import User
from app.database.services import get_services_db


def _check_admin_or_coordinator(user: User) -> None:
    """Raise 403 if user is not admin/coordinator."""
    if user.role not in ("admin", "coordinator"):
        raise HTTPException(status_code=403, detail="Access denied.")


async def create_meeting_template(
    template_data: MeetingTemplateCreate,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = None
) -> MeetingTemplate:
    """
    Create and persist a new meeting template.
    Only admins and coordinators may perform this action.

    Args:
        template_data (MeetingTemplateCreate): Data for the new meeting template.
        db (AsyncSession): Active SQLAlchemy session.

    Returns:
        MeetingTemplate: The created template object.
    """
    _check_admin_or_coordinator(current_user)

    template = MeetingTemplate(
        speciality=template_data.speciality,
        hospital=template_data.hospital,
        location=template_data.location,
        summary_id=template_data.summary_id,
        notes_form_afo_id=template_data.notes_form_afo_id,
        treatment_decision=template_data.treatment_decision,
        virtual_meeting=template_data.virtual_meeting,
        team=[member.model_dump() for member in template_data.team],
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def get_meeting_template(
    template_id: int,
    db: AsyncSession,
    current_user: User
) -> MeetingTemplate:
    """
    Retrieve a single meeting template by its ID.

    Args:
        template_id (int): ID of the template to retrieve.
        db (AsyncSession): Database session.

    Returns:
        MeetingTemplate: The requested meeting template.

    Raises:
        HTTPException: If the template is not found.
    """
    _check_admin_or_coordinator(current_user)

    result = await db.execute(select(MeetingTemplate).filter_by(id=template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Meeting template not found")
    return template


async def list_meeting_templates(
    db: AsyncSession,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
    speciality: Optional[str] = None,
    hospital: Optional[str] = None
) -> List[MeetingTemplate]:
    """
    Retrieve a paginated list of meeting templates with optional filtering.

    Args:
        db (AsyncSession): Database session.
        skip (int): Number of records to skip.
        limit (int): Max number of records to return.
        speciality (Optional[str]): Filter by speciality.
        hospital (Optional[str]): Filter by hospital.

    Returns:
        List[MeetingTemplate]: A list of meeting templates.
    """
    _check_admin_or_coordinator(current_user)

    stmt = select(MeetingTemplate)

    if speciality:
        stmt = stmt.where(MeetingTemplate.speciality == speciality)
    if hospital:
        stmt = stmt.where(MeetingTemplate.hospital == hospital)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().unique().all()


async def update_meeting_template(
    template_id: int,
    update_data: MeetingTemplateUpdate,
    db: AsyncSession,
    current_user: User
) -> MeetingTemplate:
    """
    Update an existing meeting template with new data.

    Args:
        template_id (int): ID of the template to update.
        update_data (MeetingTemplateUpdate): Data for updating the template.
        db (AsyncSession): Database session.

    Returns:
        MeetingTemplate: The updated template object.

    Raises:
        HTTPException: If the template is not found.
    """
    _check_admin_or_coordinator(current_user)

    template = await get_meeting_template(template_id, db)

    for field, value in update_data.model_dump(exclude_unset=True).items():
        if field == "team" and value is not None:
            setattr(template, field, [member.model_dump() for member in value])
        else:
            setattr(template, field, value)

    await db.commit()
    await db.refresh(template)
    return template


async def delete_meeting_template(
    template_id: int,
    db: AsyncSession,
    current_user: User
) -> None:
    """
    Delete a meeting template by its ID.

    Args:
        template_id (int): ID of the template to delete.
        db (AsyncSession): Database session.

    Raises:
        HTTPException: If the template is not found.
    """
    _check_admin_or_coordinator(current_user)

    template = await get_meeting_template(template_id, db)
    await db.delete(template)
    await db.commit()
