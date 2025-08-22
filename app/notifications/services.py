"""
notifications.services

Implements the core business logic for managing and dispatching notifications.
Includes creation, sending via multiple channels, status updates,
user preferences, and trigger evaluation.

Logging is used throughout for operational visibility and debugging.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
import operator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_, select

from app.notifications.models import NotificationStatus, Notification, WatchedItem, NotificationPreference
from app.notifications.schemas import NotificationCreate, WatchedItemCreate, NotificationPreferenceCreate
from app.notifications.utils.delivery import send_email_notification, send_whatsapp_message, save_notification_to_file
from app.calendar.models.meeting import Meeting
from app.messaging.models.messaging import Message
from app.notifications.utils.preferences import get_user_preferences


logger = logging.getLogger(__name__)

# Maps model names to their ORM classes
MODEL_LOOKUP = {
    "Meeting": Meeting,
    "Message": Message,
    # Add more models as needed
}

# Maps operator strings to Python operator functions
OPERATORS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


class NotificationService:
    """
    Service class to handle notification creation, sending, and user interactions.

    Attributes:
        db (Session): SQLAlchemy database session.
    """
    def __init__(self, db: AsyncSession):
        """
        Initialize NotificationService with a DB session.

        Args:
            db (Session): The SQLAlchemy session to use.
        """
        self.db = db


    async def create_notification(self, notif_data: NotificationCreate) -> Notification:
        """
        Create and persist a new notification.

        Args:
            notif_data (NotificationCreate): Notification input schema.

        Returns:
            Notification: Created Notification ORM object.
        """
        logger.info(f"Creating notification for user_id={notif_data.user_id} with message={notif_data.message}")
        db_notif = Notification(**notif_data.model_dump())
        self.db.add(db_notif)
        await self.db.commit()
        await self.db.refresh(db_notif)
        logger.debug(f"Notification created with ID={db_notif.id}")
        return db_notif


    async def send_notification(self, notif: Notification) -> None:
        """
        Sends the notification. For now, just updates the sent_at timestamp.

        Args:
            notif (Notification): The notification to send.
        """
        notif.sent_at = datetime.now(timezone.utc)
        logger.info(f"Sending notification ID={notif.id} to user_id={notif.user_id}")

        pref = await get_user_preferences(self.db, notif.user_id)
        methods = pref.delivery_methods if pref else ["in_app"]
        logger.debug(f"Delivery methods for notification ID={notif.id}: {methods}")

        for method in methods:
            try:
                if method == "email":
                    await send_email_notification(notif)
                    logger.debug(f"Sent email notification ID={notif.id}")
                elif method == "whatsapp":
                    await send_whatsapp_message(notif)
                    logger.debug(f"Sent WhatsApp notification ID={notif.id}")
                elif method == "file":
                    await save_notification_to_file(notif)
                    logger.debug(f"Saved notification ID={notif.id} to file")
            except Exception as e:
                logger.error(f"Error sending notification ID={notif.id} via {method}: {e}")

        await self.db.commit()
        logger.info(f"Completed sending notification ID={notif.id}")


    async def mark_as_read(self, notification_id: int) -> Notification:
        """
        Mark a notification as read.

        Args:
            notification_id (int): ID of the notification.

        Returns:
            Notification: Updated Notification object.
        """
        logger.info(f"Marking notification ID={notification_id} as read")
        notif = await self.db.get(Notification, notification_id)
        if notif is None:
            logger.warning(f"Notification ID={notification_id} not found for mark_as_read")
            raise ValueError(f"Notification ID {notification_id} not found")

        notif.status = NotificationStatus.READ
        notif.read_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(notif)
        logger.debug(f"Notification ID={notification_id} marked as read")
        return notif


    async def dismiss(self, notification_id: int) -> Notification:
        """
        Dismiss a notification.

        Args:
            notification_id (int): ID of the notification.

        Returns:
            Notification: Updated Notification object.
        """
        logger.info(f"Dismissing notification ID={notification_id}")
        notif = await self.db.get(Notification, notification_id)
        if notif is None:
            logger.warning(f"Notification ID={notification_id} not found for dismiss")
            raise ValueError(f"Notification ID {notification_id} not found")

        notif.status = NotificationStatus.DISMISSED
        await self.db.commit()
        await self.db.refresh(notif)
        logger.debug(f"Notification ID={notification_id} dismissed")
        return notif


    async def snooze(self, notification_id: int, snooze_until: datetime) -> Notification:
        """
        Snooze a notification. Future delivery logic to be implemented.

        Args:
            notification_id (int): ID of the notification.
            snooze_until (datetime): Time until which the notification is snoozed.

        Returns:
            Notification: Updated Notification object.
        """
        logger.info(f"Snoozing notification ID={notification_id} until {snooze_until.isoformat()}")
        notif = await self.db.get(Notification, notification_id)
        if notif is None:
            logger.warning(f"Notification ID={notification_id} not found for snooze")
            raise ValueError(f"Notification ID {notification_id} not found")

        notif.status = NotificationStatus.SNOOZED
        notif.snooze_until = snooze_until
        await self.db.commit()
        await self.db.refresh(notif)
        logger.debug(f"Notification ID={notification_id} snoozed until {snooze_until.isoformat()}")
        return notif


    async def get_active_notifications(self, user_id: int) -> List[Notification]:
        """
            Retrieve all active notifications for a given user.

            Active notifications are defined as:
            - Notifications with status UNREAD, or
            - Notifications with status SNOOZED where the snooze_until time has passed.

            Results are ordered by creation time in descending order.

            Args:
                user_id (int): The ID of the user for whom to fetch notifications.

            Returns:
                List[Notification]: A list of active Notification objects.
        """
        logger.info(f"Fetching active notifications for user_id={user_id}")
        now = datetime.now(timezone.utc)

        stmt = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                or_(
                    Notification.status == NotificationStatus.UNREAD,
                    and_(
                        Notification.status == NotificationStatus.SNOOZED,
                        Notification.snooze_until <= now,
                    ),
                )
            )
            .order_by(Notification.priority.desc(), Notification.created_at.desc())
        )

        result = await self.db.execute(stmt)
        notifications = result.scalars().all()
        logger.debug(f"Found {len(notifications)} active notifications for user_id={user_id}")
        return notifications


    async def watch_item(self, watch_data: WatchedItemCreate) -> WatchedItem:
        """
        Register a user-defined watch on a dynamic item.

        Args:
            watch_data (WatchedItemCreate): Data defining which item to watch and under what conditions.

        Returns:
            WatchedItem: The created WatchedItem ORM object, persisted to the database.
        """
        db_watch = WatchedItem(**watch_data.model_dump())
        self.db.add(db_watch)
        await self.db.commit()
        await self.db.refresh(db_watch)
        return db_watch


    async def evaluate_triggers(self) -> List[Notification]:
        """
        Evaluate all watched items and generate notifications based on trigger conditions.
        Supports compound rules using AND/OR logic.
        """
        logger.info("Evaluating triggers for watched items")
        notifications = []
        now = datetime.now(timezone.utc)

        stmt = select(WatchedItem)
        result = await self.db.execute(stmt)
        watched_items = result.scalars().all()

        for watch in watched_items:
            conditions = watch.trigger_conditions or {}
            logic = conditions.get("logic", "AND")
            rules = conditions.get("rules", [])

            logger.debug(f"Evaluating watch ID={watch.id} with logic={logic} and rules count={len(rules)}")

            rule_results = []

            for rule in rules:
                model_name = rule.get("model")
                field = rule.get("field")
                op = rule.get("operator")
                value = rule.get("value")

                model = MODEL_LOOKUP.get(model_name)
                if not model:
                    logger.warning(f"Unknown model '{model_name}' in watch ID={watch.id}")
                    continue

                query_value = await self._resolve_field(model, field, watch.user_id)

                op_func = OPERATORS.get(op)
                if op_func is None:
                    logger.warning(f"Unknown operator '{op}' in watch ID={watch.id}")
                    continue

                result = op_func(query_value, value)
                logger.debug(f"Rule check: model={model_name}, field={field}, op={op}, value={value}, query_value={query_value}, result={result}")
                rule_results.append(result)

            condition_met = (logic == "AND" and all(rule_results)) or (logic == "OR" and any(rule_results))
            if condition_met:
                notif = NotificationCreate(
                    user_id=watch.user_id,
                    title=f"Alert for watched {watch.item_type}",
                    body=f"Trigger condition met for item {watch.item_type}:{watch.item_id}",
                    priority="MEDIUM",
                    status="UNREAD",
                )
                created = await self.create_notification(notif)
                notifications.append(created)
                logger.info(f"Trigger condition met, notification created ID={created.id} for watch ID={watch.id}")

        logger.info(f"Evaluation complete, {len(notifications)} notifications created")
        return notifications


    async def _resolve_field(self, model, field: str, user_id: int):
        """
        Dynamically resolve a field value for a model. Custom logic per field/model goes here.
        """
        if model.__name__ == "Meeting" and field == "scheduled_within_hours":
            stmt = select(model).where(model.user_id == user_id)
            result = await self.db.execute(stmt)
            meetings = result.scalars().all()
            if not meetings:
                return float("inf")
            # Example: min time from now to any scheduled meeting
            return min([(m.scheduled_at - datetime.now(timezone.utc)).total_seconds() / 3600 for m in meetings])

        elif model.__name__ == "Metric" and field == "average_recovery_time":
            # This assumes you have a metric model to query
            stmt = select(model).where(model.user_id == user_id)
            result = await self.db.execute(stmt)
            metric = result.scalar_one_or_none()
            return getattr(metric, field, 0)

        elif hasattr(model, field):
            stmt = select(model).where(model.user_id == user_id)
            result = await self.db.execute(stmt)
            obj = result.scalar_one_or_none()
            return getattr(obj, field, None)

        return None


    async def create_or_update_preference(self, user_id: int, pref_data: NotificationPreferenceCreate) \
            -> NotificationPreference:
        """
               Create a new notification preference or update existing preferences for a user.

               This method checks if notification preferences already exist for the given user.
               If preferences exist, it updates the fields with the provided data.
               Otherwise, it creates a new preference entry.

               Args:
                   user_id (int): The ID of the user whose preferences are being created or updated.
                   pref_data (NotificationPreferenceCreate): Data containing the preference settings.

               Returns:
                   NotificationPreference: The created or updated NotificationPreference ORM instance.
        """
        logger.info(f"Creating or updating notification preferences for user_id={user_id}")
        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            for field, value in pref_data.model_dump().items():
                setattr(existing, field, value)
            existing.updated_at = datetime.now(timezone.utc)
            logger.debug(f"Updated preferences for user_id={user_id}")
        else:
            existing = NotificationPreference(user_id=user_id, **pref_data.model_dump())
            self.db.add(existing)
            logger.debug(f"Created new preferences for user_id={user_id}")

        await self.db.commit()
        await self.db.refresh(existing)
        return existing
