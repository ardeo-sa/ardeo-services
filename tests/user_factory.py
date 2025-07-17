"""
Factory for creating User model instances for testing.

This factory uses the `factory_boy` library to generate realistic fake user data.
It should be used in tests to avoid manually creating User instances.
"""

import uuid
import factory
from app.users.models.user import User


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """
    Factory for the `User` SQLAlchemy model.

    Attributes:
        id (UUID): Automatically generated unique user ID.
        email (str): Fake email address.
        first_name (str): Fake first name.
        last_name (str): Fake last name.
        role (str): Default role set to "normal".

    Note:
        - `sqlalchemy_session` must be set in test setup.
        - Instances are committed to the database due to `sqlalchemy_session_persistence = "commit"`.
    """
    class Meta:
        """
        Configuration for SQLAlchemyModelFactory.

        - model: Specifies the SQLAlchemy model to instantiate.
        - sqlalchemy_session: A test-provided session for database operations. Must be set externally.
        - sqlalchemy_session_persistence: 'commit' means each created object is committed immediately.
        """
        model = User
        sqlalchemy_session = None  # Set this during test setup
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = "normal"
