import factory
from app.users.models.user import User
from app.database.services import get_services_db

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = get_services_db()
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n + 1)
    email = factory.Faker("email")
    role = "user"
