"""
API routes for managing meeting templates.

These endpoints allow creation, retrieval, update, and deletion of meeting templates.
Access is restricted to admin and coordinator roles.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.calendar.schemas.meeting_template import (
    MeetingTemplateBase,
    MeetingTemplateResponse,
    MeetingTemplateUpdate
)
from app.users.models.user import User
from app.database.services import get_services_db
from app.core.dependencies import get_current_user
from app.calendar.services.meeting_template import (
    create_meeting_template,
    get_meeting_template,
    list_meeting_templates,
    update_meeting_template,
    delete_meeting_template,
)

router = APIRouter(tags=["Meeting Templates"])
logger = logging.getLogger("calendar.meeting_templates")



def _check_admin_or_coordinator(user: User):
    """Utility to enforce RBAC for meeting template routes."""
    if user.role not in ("admin", "coordinator"):
        logger.warning(f"Unauthorized access attempt by user {user.id} ({user.role})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and coordinators can manage meeting templates.",
        )


# --- Routes ---
@router.post("/", response_model=MeetingTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_in: MeetingTemplateBase,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new meeting template.
    Only accessible to admins and coordinators.
    """
    _check_admin_or_coordinator(current_user)

    logger.info(f"User {current_user.id} creating meeting template: {template_in.title}")
    return await create_meeting_template(template_in, db)


@router.get("/{template_id}", response_model=MeetingTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a single meeting template by ID.
    Only accessible to admins and coordinators.
    """
    _check_admin_or_coordinator(current_user)

    logger.debug(f"User {current_user.id} fetching meeting template {template_id}")
    return await get_meeting_template(template_id, db)


@router.get("/", response_model=List[MeetingTemplateResponse])
async def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all meeting templates with pagination.
    Only accessible to admins and coordinators.
    """
    _check_admin_or_coordinator(current_user)

    logger.debug(f"User {current_user.id} listing meeting templates (skip={skip}, limit={limit})")
    return await list_meeting_templates(skip=skip, limit=limit, db=db)


@router.put("/{template_id}", response_model=MeetingTemplateResponse)
async def update_template(
    template_id: int,
    template_in: MeetingTemplateUpdate,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing meeting template.
    Only accessible to admins and coordinators.
    """
    _check_admin_or_coordinator(current_user)

    logger.info(f"User {current_user.id} updating meeting template {template_id}")
    return await update_meeting_template(template_id, template_in, db)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_services_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a meeting template.
    Only accessible to admins and coordinators.
    """
    _check_admin_or_coordinator(current_user)

    logger.warning(f"User {current_user.id} deleting meeting template {template_id}")
    await delete_meeting_template(template_id, db)
    return {"detail": f"Meeting template {template_id} deleted"}
