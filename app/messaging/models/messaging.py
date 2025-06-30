"""
SQLAlchemy ORM models for the messaging feature in the healthcare web app.

Defines the `Conversation` and `Message` database tables, which support private
messaging between two users. Each conversation contains multiple messages,
and each message includes metadata such as sender, receiver, timestamp, and read status.
"""
# from datetime import datetime
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.types import JSON, Uuid
from sqlalchemy import Column, DateTime, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON

from app.database.services import Base
from app.database.types import UUIDListJSON

class Conversation(Base):
    """
        Represents a private conversation between two users.

        Attributes:
            id (UUID): Primary key, unique identifier for the conversation.
            user1_id (UUID): ID of the first user.
            user2_id (UUID): ID of the second user.
            created_at (datetime): Timestamp of when the conversation was created.
            messages (List[Message]): One-to-many relationship to messages in this conversation.
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    topic = Column(String, nullable=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    participant_ids = Column(
        ARRAY(UUID(as_uuid=True)).with_variant(UUIDListJSON, "sqlite"),
        nullable=False
    )

    # Relationships
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    """
        Represents a single message sent between two users in a conversation.

        Attributes:
            id (UUID): Primary key, unique identifier for the message.
            conversation_id (UUID): Foreign key referencing the parent conversation.
            sender_id (UUID): ID of the user who sent the message.
            receiver_id (UUID): ID of the user receiving the message.
            content (str): The text content of the message.
            timestamp (datetime): Timestamp of when the message was sent.
            read (bool): Whether the message has been read by the receiver.
            conversation (Conversation): Relationship to the parent conversation.
    """
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    read = Column(Boolean, default=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
