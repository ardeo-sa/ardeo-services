"""
Custom SQLAlchemy column type for storing lists of UUIDs.

This module defines `UUIDListJSON`, a SQLAlchemy `TypeDecorator` that
stores Python lists of `uuid.UUID` objects as JSON in the database.

- On SQLite, the UUIDs are stored as JSON strings.
- On PostgreSQL, they can be stored as native UUID values if the database
  driver supports it.
- When reading from the database, JSON strings are automatically converted
  back into `uuid.UUID` instances.

Typical usage:

    from sqlalchemy import Column
    from app.db.types import UUIDListJSON

    class MyModel(Base):
        __tablename__ = "my_table"
        ids = Column(UUIDListJSON)

    obj = MyModel(ids=[uuid.uuid4(), uuid.uuid4()])
    session.add(obj)

Logging:
    Logs the data before saving to and after loading from the database.
"""

import uuid
import logging
from sqlalchemy.types import TypeDecorator, JSON

logger = logging.getLogger(__name__)

class UUIDListJSON(TypeDecorator):
    """Stores list of UUIDs as JSON strings in SQLite, as native UUIDs in Postgres."""
    impl = JSON

    def process_bind_param(self, value, dialect):
        """Convert UUID objects to strings before saving to DB."""
        logger.debug("Binding UUID list to DB: %s", value)
        if value is None:
            return value
        processed = [str(v) if isinstance(v, uuid.UUID) else v for v in value]
        logger.debug("Processed UUID list for DB: %s", processed)
        return processed

    def process_result_value(self, value, dialect):
        """Convert stored strings back to UUID objects after loading from DB."""
        logger.debug("Loading UUID list from DB: %s", value)
        if value is None:
            return value
        processed = [uuid.UUID(v) for v in value]
        logger.debug("Processed UUID list from DB: %s", processed)
        return processed
