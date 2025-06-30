from sqlalchemy.types import TypeDecorator, JSON
import uuid

class UUIDListJSON(TypeDecorator):
    """Stores list of UUIDs as JSON strings in SQLite, as native UUIDs in Postgres."""
    impl = JSON

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return [str(v) if isinstance(v, uuid.UUID) else v for v in value]

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return [uuid.UUID(v) for v in value]
