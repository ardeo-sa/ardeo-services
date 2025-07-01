"""
Pydantic schemas for messaging functionality.

This module defines the data models used for creating, retrieving, and serializing
messages and conversations between users. These schemas support data validation
and automatic documentation generation for FastAPI endpoints related to messaging.

Schemas:
- MessageCreate: For creating a new message.
- MessageOut: For returning message data via the API.
- ConversationOut: For returning a conversation along with its messages.
- ConversationCreate: For initiating a new conversation between two users.
"""
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class MessageCreate(BaseModel):
    """
        Schema for creating a new message.

        Attributes:
            conversation_id (UUID): The ID of the conversation the message belongs to.
            sender_id (UUID): The ID of the user sending the message.
            recipient_id (UUID): The ID of the user receiving the message.
            content (str): The content of the message.
    """
    conversation_id: UUID
    sender_id: UUID
    recipient_id: UUID
    content: str

    model_config = {
        "from_attributes": True
    }


class MessageOut(BaseModel):
    """
        Schema for returning a message from the API.

        Attributes:
            id (UUID): Unique identifier for the message.
            conversation_id (UUID): The ID of the conversation the message belongs to.
            sender_id (UUID): The ID of the user who sent the message.
            recipient_id (UUID): The ID of the user who received the message.
            content (str): The content of the message.
            timestamp (datetime): When the message was sent.
            read (bool): Whether the message has been read by the recipient.
    """
    id: UUID
    sender_id: UUID
    timestamp: datetime
    read: bool
    content: str

    model_config = {
        "from_attributes": True
    }


class ConversationOut(BaseModel):
    """
        Schema for returning a conversation with its messages.

        Attributes:
            id (UUID): Unique identifier for the conversation.
            user1_id (UUID): The ID of the first user in the conversation.
            user2_id (UUID): The ID of the second user in the conversation.
            created_at (datetime): When the conversation was created.
            messages (List[MessageOut]): List of messages exchanged in this conversation.
    """
    id: UUID
    created_at: datetime
    messages: List[MessageOut]
    topic: Optional[str]
    meeting_id: Optional[int]

    model_config = {
        "from_attributes": True
    }


class ConversationCreate(BaseModel):
    """
    Schema for creating a new conversation between two users.

    Attributes:
        user1_id (UUID): The ID of the first user initiating the conversation.
        user2_id (UUID): The ID of the second user in the conversation.
    """
    participant_ids: List[UUID]
    topic: Optional[str] = None
    meeting_id: Optional[int] = None  # if linked to MDT

    model_config = {
        "from_attributes": True
    }
