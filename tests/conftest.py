import pytest

from app import create_app, db
from models import Role, User


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        }
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def create_user(app):
    def _create_user(email: str, employee_approved: bool, role: Role = Role.EMPLOYEE) -> int:
        user = User(email=email, role=role, employee_approved=employee_approved)
        db.session.add(user)
        db.session.commit()
        return user.id

    return _create_user
