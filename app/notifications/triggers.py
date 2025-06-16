"""
notifications.triggers

Defines functions that act as triggers for creating notifications based on specific events.
"""
from sqlalchemy.orm import Session

from .service import NotificationService
from .schemas import NotificationCreate

def notify_step_completed(db: Session, user_id: int, patient_id: int, step_id: int):
    """
    Notify a user when a patient pathway step is completed.

    Args:
        db (Session): DB session.
        user_id (int): Target user ID.
        patient_id (int): Related patient ID.
        step_id (int): Completed pathway step ID.

    Returns:
        Notification: Created notification object.
    """
    message = f"Pathway step {step_id} for patient {patient_id} has been completed."
    service = NotificationService(db)
    notif = NotificationCreate(
        user_id=user_id,
        patient_id=patient_id,
        pathway_step_id=step_id,
        message=message
    )
    return service.create_notification(notif)

def notify_task_assigned(db: Session, user_id: int, task_id: int):
    """
    Notify a user when a new task is assigned.

    Args:
        db (Session): DB session.
        user_id (int): Target user ID.
        task_id (int): Assigned task ID.

    Returns:
        Notification: Created notification object.
    """
    message = f"A new task (ID: {task_id}) has been assigned to you."
    service = NotificationService(db)
    notif = NotificationCreate(
        user_id=user_id,
        task_id=task_id,
        message=message
    )
    return service.create_notification(notif)
