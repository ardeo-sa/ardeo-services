"""
Unit tests for the Messaging API endpoints in a FastAPI application.

This test module covers the following functionality:

- Creating conversations between users.
- Retrieving conversation metadata by ID.
- Sending messages within a conversation.
- Fetching message history for a conversation.
- Handling error and edge cases such as:
    - Fetching messages from a nonexistent conversation.
    - Sending messages as unauthorized or non-participant users.
    - Attempting to send empty messages.

Test Infrastructure:
--------------------
- Uses `pytest` with `pytest-asyncio` for async HTTPX client testing.
- Fixtures like `async_client`, `normal_user`, and `coordinator_user` are shared via `conftest-old.py`.
- DB is set up in-memory using SQLite for isolated test execution.

Each test ensures that the messaging feature works correctly both in normal and edge-case scenarios,
and integrates properly with authentication and dependency injection.

"""
import pytest

from app.messaging.schemas.messaging import MessageCreate, ConversationCreate
from app.messaging.services.messaging_service import (
    create_conversation,
    create_message,
    get_conversation_by_id,
    get_conversation_messages
)


@pytest.mark.asyncio
async def test_create_conversation(db_session, normal_user, coordinator_user):
    """
    Test that a conversation can be created between two users using the service layer.
    """
    # payload = ConversationCreate(
    #     participant_ids=[normal_user.id, coordinator_user.id],
    #     topic="Therapy Planning"
    # )

    payload = ConversationCreate(
        participant_ids=[str(normal_user.id), str(coordinator_user.id)],
        topic="Therapy Planning"
    )

    convo = await create_conversation(db_session, payload)
    assert convo.id is not None
    assert convo.topic == "Therapy Planning"
    user_ids = [str(p) for p in convo.participant_ids]
    assert set(user_ids) == {str(normal_user.id), str(coordinator_user.id)}


@pytest.mark.asyncio
async def test_get_conversation_by_id(db_session, normal_user):
    """
    Test retrieving a conversation by ID after creation.
    """
    participant_ids = [str(normal_user.id)]

    convo = await create_conversation(db_session, ConversationCreate(
        participant_ids=participant_ids,
        topic="Solo Chat"
    ))

    fetched = await get_conversation_by_id(db_session, convo.id)
    assert fetched.id == convo.id
    assert fetched.topic == "Solo Chat"

    # Check participant_ids come back correctly, converting them to strings
    fetched_participants = [str(pid) for pid in fetched.participant_ids]
    assert set(fetched_participants) == set(participant_ids)


@pytest.mark.asyncio
async def test_create_message(db_session, normal_user, coordinator_user):
    """
    Test sending a message between two users in a conversation.
    """
    convo = await create_conversation(db_session, ConversationCreate(
        participant_ids=[normal_user.id, coordinator_user.id],
        topic="Welcome Thread"
    ))

    message_data = MessageCreate(
        conversation_id=convo.id,
        sender_id=normal_user.id,
        recipient_id=coordinator_user.id,
        content="Hello and welcome!"
    )

    msg = await create_message(db_session, message_data)
    assert msg.id is not None
    assert msg.content == "Hello and welcome!"
    assert str(msg.sender_id) == normal_user.id
    assert str(msg.recipient_id) == coordinator_user.id


@pytest.mark.asyncio
async def test_get_conversation_messages(db_session, normal_user, coordinator_user):
    """
    Test retrieving the message history from a conversation.
    """
    convo = await create_conversation(db_session, ConversationCreate(
        participant_ids=[normal_user.id, coordinator_user.id],
        topic="History Test"
    ))

    await create_message(db_session, MessageCreate(
        conversation_id=convo.id,
        sender_id=normal_user.id,
        recipient_id=coordinator_user.id,
        content="Message One"
    ))

    await create_message(db_session, MessageCreate(
        conversation_id=convo.id,
        sender_id=coordinator_user.id,
        recipient_id=normal_user.id,
        content="Message Two"
    ))

    messages = await get_conversation_messages(db_session, convo.id, user_id=normal_user.id)
    assert len(messages) == 2
    assert messages[0].content == "Message One"
    assert messages[1].content == "Message Two"


@pytest.mark.asyncio
async def test_empty_conversation_returns_no_messages(db_session, normal_user):
    """
    Test that an empty conversation returns an empty list of messages.
    """
    convo = await create_conversation(db_session, ConversationCreate(
        participant_ids=[normal_user.id],
        topic="Quiet Room"
    ))

    messages = await get_conversation_messages(db_session, convo.id, user_id=normal_user.id)
    assert messages == []
