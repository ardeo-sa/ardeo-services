"""
Messaging service module for handling conversation messages in the Ardeo-services app.

This module provides functions to create and retrieve messages and conversations,
including enforcement of access control for MDT-related messaging.

Functions:
    - create_message: Stores a new message in the database with role-based checks.
    - get_conversation_messages: Retrieves all messages for a conversation with access validation.
    - create_conversation: Creates a new conversation, optionally linked to an MDT meeting.
    - get_conversation_by_id: Fetches a single conversation by ID.
    - is_mdt_conversation: Determines if a conversation is linked to an MDT meeting.
    - user_can_access_mdt: Checks if a user has rights to participate in MDT conversation.
"""
import logging
from uuid import UUID
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.calendar.models.meeting import MeetingParticipant
from app.messaging.models.messaging import Message, Conversation
from app.messaging.schemas.messaging import MessageCreate, ConversationCreate

logger = logging.getLogger(__name__)


async def create_message(db: AsyncSession, message: MessageCreate) -> Message:
    """
    Create a new message in the database and enforce MDT access control if needed.

    Args:
        db (Session): SQLAlchemy DB session.
        message (MessageCreate): Incoming message data.

    Returns:
        Message: Created message instance.

    Raises:
        HTTPException: If user is not authorized to send messages in MDT conversation.
    """
    logger.info("Creating message in conversation %s from sender %s",
                message.conversation_id, message.sender_id)

    conversation = await get_conversation_by_id(db, message.conversation_id)
    if not conversation:
        logger.warning("Conversation not found: %s", message.conversation_id)
        raise HTTPException(status_code=404, detail="Conversation not found")

    if await is_mdt_conversation(conversation):
        logger.debug("Conversation %s is MDT-linked. Checking access for user %s",
                     message.conversation_id, message.sender_id)
        if not await user_can_access_mdt(conversation, message.sender_id, db):
            logger.warning("User %s not authorized to post in MDT conversation %s",
                           message.sender_id, message.conversation_id)
            raise HTTPException(status_code=403, detail="User not authorized to post in MDT channel")

    msg = Message(
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        recipient_id=message.recipient_id,
        content=message.content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    logger.debug("Message %s created in conversation %s", msg.id, message.conversation_id)
    return msg


async def get_conversation_messages(db: AsyncSession, conversation_id: UUID, user_id: UUID) -> List[Message]:
    """
    Retrieve all messages for a conversation, enforcing MDT access control.

    Args:
        db (Session): SQLAlchemy DB session.
        conversation_id (UUID): ID of the conversation.
        user_id (UUID): ID of the requesting user.

    Returns:
        List[Message]: Chronologically ordered messages.

    Raises:
        HTTPException: If access is denied or conversation doesn't exist.
    """
    logger.info("Fetching messages for conversation %s (requested by user %s)",
                conversation_id, user_id)

    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        logger.warning("Conversation %s not found", conversation_id)
        raise HTTPException(status_code=404, detail="Conversation not found")

    if await is_mdt_conversation(conversation):
        logger.debug("Conversation %s is MDT-linked. Checking access for user %s",
                     conversation_id, user_id)
        if not await user_can_access_mdt(conversation, user_id, db):
            logger.warning("User %s not authorized to access MDT conversation %s",
                           user_id, conversation_id)
            raise HTTPException(status_code=403, detail="User not authorized to access MDT conversation")


    stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp)
    result = await db.execute(stmt)
    messages = result.scalars().all()

    logger.debug("Fetched %d messages for conversation %s", len(messages), conversation_id)
    return messages


async def create_conversation(db: AsyncSession, conversation: ConversationCreate) -> Conversation:
    """
    Create a new conversation with the specified participants.

    Args:
        db (Session): The SQLAlchemy session.
        conversation (ConversationCreate): Conversation participants and optional topic.

    Returns:
        Conversation: The newly created conversation object.
    """
    logger.info("Creating conversation with participants: %s", conversation.participant_ids)

    new_convo = Conversation(
        participant_ids=conversation.participant_ids,
        topic=conversation.topic,
    )
    db.add(new_convo)
    await db.commit()
    await db.refresh(new_convo)

    logger.debug("Created conversation %s", new_convo.id)
    return new_convo


async def get_conversation_by_id(db: AsyncSession, conversation_id: UUID) -> Conversation:
    """
    Retrieve a conversation object by its UUID.

    Args:
        db (Session): The SQLAlchemy session.
        conversation_id (UUID): The ID of the conversation.

    Returns:
        Conversation: The conversation instance.

    Raises:
        HTTPException: If no conversation is found with the given ID.
    """
    logger.debug("Looking up conversation %s", conversation_id)

    stmt = select(Conversation).where(Conversation.id == conversation_id).order_by(Conversation.created_at)
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if conversation:
        logger.debug("Found conversation %s", conversation_id)
    else:
        logger.debug("No conversation found for %s", conversation_id)

    return conversation


async def is_mdt_conversation(conversation: Conversation) -> bool:
    """
    Determine whether a given conversation is linked to an MDT meeting.

    Args:
        conversation (Conversation): The conversation instance.

    Returns:
        bool: True if it is an MDT-linked conversation; False otherwise.
    """
    return conversation.meeting_id is not None


async def user_can_access_mdt(conversation: Conversation, user_id: UUID, db: AsyncSession) -> bool:
    """
        Check whether a user is a participant in the MDT meeting tied to a conversation.

        Args:
            conversation (Conversation): The MDT-linked conversation.
            user_id (UUID): The ID of the user attempting to access.
            db (Session): SQLAlchemy DB session.

        Returns:
            bool: True if the user is a valid MDT participant, False otherwise.
    """
    meeting_id = conversation.meeting_id
    if not meeting_id:
        return True  # Not MDT-bound

    logger.debug("Checking MDT participant status for user %s in meeting %s", user_id, meeting_id)

    # Async-safe query
    stmt = select(MeetingParticipant).filter_by(meeting_id=meeting_id, user_id=user_id)
    result = await db.execute(stmt)
    participant = result.scalar_one_or_none()

    allowed = participant is not None
    logger.debug("User %s MDT access: %s", user_id, allowed)
    return allowed