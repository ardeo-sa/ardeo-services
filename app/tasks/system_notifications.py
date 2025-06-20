"""
Background tasks for generating predefined system notifications.

This module includes logic to detect:
- Overdue or completed care steps
- MDT meeting assignments
- Newly assigned tasks
- Available clinical reports

It includes both:
- Async business logic for notification generation
- Celery-compatible sync wrapper for scheduling

Intended to be triggered via Celery or manually.
"""

import asyncio
import logging
from typing import List
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from celery import shared_task
from app.database.session import async_session_maker

from app.notifications.models import Notification
from app.notifications.schemas import NotificationCreate
from app.notifications.enums import NotificationType
from app.notifications.service import NotificationService

from app.patients.models import CareStep  # hypothetical model
from app.meetings.models import MDTAssignment  # hypothetical model
from app.tasks.models import Task  # hypothetical model
from app.reports.models import ClinicalReport  # hypothetical model

logger = logging.getLogger(__name__)

!!TODO generate the missing models

async def generate_system_notifications(db: AsyncSession) -> List[Notification]:
    """
    Automatically generate predefined system notifications.

    Trigger scenarios:
    - Overdue or completed care steps
    - New MDT assignments
    - New tasks assigned
    - Clinical reports uploaded

    Args:
        db (AsyncSession): Database session

    Returns:
        List[Notification]: List of created notifications
    """
    service = NotificationService(db)
    created = []

    now = datetime.now(timezone.utc)

    # 1. Overdue Care Steps
    result = await db.execute(select(CareStep).where(
        and_(CareStep.due_date < now, CareStep.completed_at == None)
    ))
    for step in result.scalars():
        notif = await service.create_notification(NotificationCreate(
            user_id=step.owner_id,
            message=f"Care step '{step.name}' for patient {step.patient_id} is overdue.",
            type=NotificationType.IN_APP,
            patient_id=step.patient_id,
            pathway_step_id=step.id,
        ))
        created.append(notif)

    # 2. New MDT Assignments
    result = await db.execute(select(MDTAssignment).where(MDTAssignment.notified == False))
    for mdt in result.scalars():
        notif = await service.create_notification(NotificationCreate(
            user_id=mdt.user_id,
            message=f"You've been assigned to MDT meeting {mdt.meeting_id}.",
            type=NotificationType.IN_APP,
        ))
        mdt.notified = True
        created.append(notif)

    # 3. New Tasks
    result = await db.execute(select(Task).where(Task.notified == False))
    for task in result.scalars():
        notif = await service.create_notification(NotificationCreate(
            user_id=task.assignee_id,
            message=f"New task assigned: {task.title}",
            type=NotificationType.IN_APP,
            task_id=task.id,
        ))
        task.notified = True
        created.append(notif)

    # 4. New Clinical Reports
    result = await db.execute(select(ClinicalReport).where(
        and_(
            ClinicalReport.uploaded_at != None,
            ClinicalReport.notified == False
        )
    ))
    for report in result.scalars():
        notif = await service.create_notification(NotificationCreate(
            user_id=report.reviewer_id,
            message=f"Clinical report (type: {report.report_type}) is ready for review.",
            type=NotificationType.IN_APP,
        ))
        report.notified = True
        created.append(notif)

    await db.commit()
    return created


@shared_task
def generate_system_notifications_task():
    """
    Celery task entry point for generating system notifications.
    Wraps the async logic in a synchronous Celery-compatible function.
    """
    try:
        asyncio.run(_run_async_task())
    except Exception as e:
        logger.exception(f"[Celery] Error generating system notifications: {e}")

async def _run_async_task():
    async with async_session_maker() as session:
        created = await generate_system_notifications(session)
        logger.info(f"[SystemNotifications] {len(created)} notifications generated")
