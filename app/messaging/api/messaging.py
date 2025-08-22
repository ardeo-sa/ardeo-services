"""
Messaging API endpoints for managing conversations and exchanging messages between users.

These FastAPI routes are mounted under the `/api/messages` prefix and allow clients to:
    - Create conversations between participants.
    - Send messages within a conversation.
    - Fetch the full message history of a specific conversation.
    - Retrieve individual conversation metadata.

Security:
    All endpoints require authentication via `get_current_user` where applicable.
"""

import logging
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.services import get_services_db
from app.messaging.schemas.messaging import (
    MessageCreate, MessageOut,
    ConversationCreate, ConversationOut
)
from app.messaging.services.messaging_service import (
    create_message, get_conversation_messages,
    create_conversation, get_conversation_by_id
)
from app.users.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["Messaging"])


@router.post("/conversations/", response_model=ConversationOut)
async def create_conversation_endpoint(
    conversation: ConversationCreate,
    db: AsyncSession = Depends(get_services_db)
):
    """
    Create a new conversation between users.

    Args:
        conversation (ConversationCreate): List of participant UUIDs and optional topic.
        db (Session): SQLAlchemy session.

    Returns:
        ConversationOut: The created conversation.
    """
    logger.info("Creating conversation with participants: %s", conversation.participants)
    result = await create_conversation(db, conversation)
    logger.debug("Created conversation: %s", result)
    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation_endpoint(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_services_db)
):
    """
    Retrieve metadata about a specific conversation.

    Args:
        conversation_id (UUID): The UUID of the conversation.
        db (Session): SQLAlchemy session.

    Raises:
        HTTPException: If the conversation does not exist.

    Returns:
        ConversationOut: Conversation details including participants and topic.
    """
    logger.info("Fetching conversation metadata for ID: %s", conversation_id)
    result = await get_conversation_by_id(db, conversation_id)
    if not result:
        logger.warning("Conversation not found: %s", conversation_id)
        raise HTTPException(status_code=404, detail="Conversation not found")
    logger.debug("Fetched conversation: %s", result)
    return result


@router.post("/", response_model=MessageOut)
async def send_message(message: MessageCreate, db: AsyncSession = Depends(get_services_db)):
    """
    Send a new message within a conversation.

    Args:
        message (MessageCreate): The message data including sender, recipient, and content.
        db (Session): The SQLAlchemy session (injected via dependency).

    Returns:
        MessageOut: The created message with metadata (e.g., timestamp, ID).
    """
    logger.info(
        "Sending message in conversation %s from sender %s",
        message.conversation_id, message.sender_id
    )
    result = await create_message(db, message)
    logger.debug("Message sent: %s", result)
    return result


@router.get("/{conversation_id}", response_model=List[MessageOut])
async def fetch_messages(conversation_id: UUID, db: AsyncSession = Depends(get_services_db),
                   current_user: User = Depends(get_current_user)):
    """
        Retrieve all messages from a specific conversation.

        Args:
            conversation_id (UUID): The unique identifier for the conversation.
            db (Session): The SQLAlchemy session (injected via dependency).

        Raises:
            HTTPException: 404 error if the conversation does not exist or contains no messages.

        Returns:
            List[MessageOut]: A list of messages in the conversation, ordered chronologically.
    """
    logger.info(
        "User %s fetching messages for conversation %s",
        current_user.id, conversation_id
    )
    messages = await get_conversation_messages(db, conversation_id, user_id=current_user.id)
    if not messages:
        logger.warning("No messages found for conversation %s", conversation_id)
        raise HTTPException(status_code=404, detail="Conversation not found or empty")
    logger.debug("Fetched %d messages for conversation %s", len(messages), conversation_id)
    return messages
