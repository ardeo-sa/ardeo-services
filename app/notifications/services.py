"""
Implements the core business logic for managing and dispatching notifications.
"""
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
        db_notif = Notification(**notif_data.model_dump())
        self.db.add(db_notif)
        await self.db.commit()
        await self.db.refresh(db_notif)
        return db_notif

    async def send_notification(self, notif: Notification) -> None:
        """
        Sends the notification. For now, just updates the sent_at timestamp.

        Args:
            notif (Notification): The notification to send.
        """
        notif.sent_at = datetime.now(timezone.utc)

        # Get delivery methods from preference
        pref = await get_user_preferences(self.db, notif.user_id)
        methods = pref.delivery_methods if pref else ["in_app"]

        for method in methods:
            if method == "email":
                await send_email_notification(notif)
            elif method == "whatsapp":
                await send_whatsapp_message(notif)
            elif method == "file":
                await save_notification_to_file(notif)

        await self.db.commit()

    async def mark_as_read(self, notification_id: int) -> Notification:
        """
        Mark a notification as read.

        Args:
            notification_id (int): ID of the notification.

        Returns:
            Notification: Updated Notification object.
        """
        notif = await self.db.get(Notification, notification_id)

        if notif is None:
            raise ValueError(f"Notification ID {notification_id} not found")

        notif.status = NotificationStatus.READ
        notif.read_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(notif)
        return notif

    async def dismiss(self, notification_id: int) -> Notification:
        """
        Dismiss a notification.

        Args:
            notification_id (int): ID of the notification.

        Returns:
            Notification: Updated Notification object.
        """
        notif = await self.db.get(Notification, notification_id)

        if notif is None:
            raise ValueError(f"Notification ID {notification_id} not found")

        notif.status = NotificationStatus.DISMISSED
        await self.db.commit()
        await self.db.refresh(notif)
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
        notif = await self.db.get(Notification, notification_id)
        if notif is None:
            raise ValueError(f"Notification ID {notification_id} not found")

        notif.status = NotificationStatus.SNOOZED
        notif.snooze_until = snooze_until
        await self.db.commit()
        await self.db.refresh(notif)
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
        return result.scalars().all()


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
        notifications = []
        now = datetime.now(timezone.utc)

        stmt = select(WatchedItem)
        result = await self.db.execute(stmt)
        watched_items = result.scalars().all()

        for watch in watched_items:
            conditions = watch.trigger_conditions or {}
            logic = conditions.get("logic", "AND")
            rules = conditions.get("rules", [])

            rule_results = []

            for rule in rules:
                model_name = rule.get("model")
                field = rule.get("field")
                op = rule.get("operator")
                value = rule.get("value")

                model = MODEL_LOOKUP.get(model_name)
                if not model:
                    continue  # unknown model

                # You may need custom logic per model/field here
                query_value = await self._resolve_field(model, field, watch.user_id)

                op_func = OPERATORS.get(op)
                if op_func is None:
                    continue  # unknown operator

                rule_results.append(op_func(query_value, value))

            if (logic == "AND" and all(rule_results)) or (logic == "OR" and any(rule_results)):
                notif = NotificationCreate(
                    user_id=watch.user_id,
                    title=f"Alert for watched {watch.item_type}",
                    body=f"Trigger condition met for item {watch.item_type}:{watch.item_id}",
                    priority="MEDIUM",  # or derive from conditions
                    status="UNREAD",
                )
                created = await self.create_notification(notif)
                notifications.append(created)

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
        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            for field, value in pref_data.model_dump().items():
                setattr(existing, field, value)
            existing.updated_at = datetime.now(timezone.utc)
        else:
            existing = NotificationPreference(user_id=user_id, **pref_data.model_dump())
            self.db.add(existing)

        await self.db.commit()
        await self.db.refresh(existing)
        return existing
