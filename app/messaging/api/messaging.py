"""
Messaging API endpoints for managing conversations and exchanging messages between users.

This module defines FastAPI routes under the /api/messages prefix, allowing clients to:
    - Create conversations between participants.
    - Send messages within a conversation.
    - Fetch the full message history of a specific conversation.
    - Retrieve individual conversation metadata.
"""
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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

router = APIRouter(prefix="/api/messages", tags=["Messaging"])


@router.post("/conversations/", response_model=ConversationOut)
def create_conversation_endpoint(
    conversation: ConversationCreate,
    db: Session = Depends(get_services_db)
):
    """
    Create a new conversation between users.

    Args:
        conversation (ConversationCreate): List of participant UUIDs and optional topic.
        db (Session): SQLAlchemy session.

    Returns:
        ConversationOut: The created conversation.
    """
    return create_conversation(db, conversation)


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation_endpoint(
    conversation_id: UUID,
    db: Session = Depends(get_services_db)
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
    return get_conversation_by_id(db, conversation_id)


@router.post("/", response_model=MessageOut)
def send_message(message: MessageCreate, db: Session = Depends(get_services_db)):
    """
    Send a new message within a conversation.

    Args:
        message (MessageCreate): The message data including sender, recipient, and content.
        db (Session): The SQLAlchemy session (injected via dependency).

    Returns:
        MessageOut: The created message with metadata (e.g., timestamp, ID).
    """
    return create_message(db, message)

@router.get("/{conversation_id}", response_model=List[MessageOut])
def fetch_messages(conversation_id: UUID, db: Session = Depends(get_services_db),
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
    messages = get_conversation_messages(db, conversation_id, user_id=current_user.id)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found or empty")
    return messages
