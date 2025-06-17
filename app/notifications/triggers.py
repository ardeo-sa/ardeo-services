"""
notifications.triggers

Defines triggers for creating notifications based on specific application events.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.service import NotificationService
from app.notifications.schemas import NotificationCreate


class NotificationTriggerService:
    """
    Service to handle business triggers that generate user notifications.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)

    async def notify_step_completed(self, user_id: int, patient_id: int, step_id: int):
        """
        Notify a user when a patient pathway step is completed.
        """
        message = f"Pathway step {step_id} for patient {patient_id} has been completed."
        notif = NotificationCreate(
            user_id=user_id,
            patient_id=patient_id,
            pathway_step_id=step_id,
            message=message,
            created_at=datetime.now(timezone.utc),
        )
        return await self.notification_service.create(notif)

    async def notify_task_assigned(self, user_id: int, task_id: int):
        """
        Notify a user when a new task is assigned.
        """
        message = f"A new task (ID: {task_id}) has been assigned to you."
        notif = NotificationCreate(
            user_id=user_id,
            task_id=task_id,
            message=message,
            created_at=datetime.now(timezone.utc),
        )
        return await self.notification_service.create(notif)

    async def notify_mdt_assignment(self, user_id: int, patient_id: int, meeting_id: int):
        """
        Notify when a patient is assigned to an MDT meeting.
        """
        message = f"Patient {patient_id} has been assigned to MDT meeting {meeting_id}."
        notif = NotificationCreate(
            user_id=user_id,
            patient_id=patient_id,
            meeting_id=meeting_id,
            message=message,
            created_at=datetime.now(timezone.utc),
        )
        return await self.notification_service.create(notif)

    async def notify_report_uploaded(self, user_id: int, report_type: str, report_id: int, patient_id: int):
        """
        Notify a user when a new report is uploaded and ready.
        """
        message = f"{report_type.capitalize()} report (ID: {report_id}) for patient {patient_id} is ready for review."
        notif = NotificationCreate(
            user_id=user_id,
            patient_id=patient_id,
            message=message,
            created_at=datetime.now(timezone.utc),
        )
        return await self.notification_service.create(notif)
