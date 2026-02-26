from app import db
from models import User


def _create_session_user(client, email="account@example.com"):
    user = User(
        email=email,
        password_hash="pbkdf2:sha256:1$dummy$dummy",
        employee_approved=True,
        full_name="Account User",
    )
    db.session.add(user)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["current_user_id"] = user.id

    return user


def test_account_pages_require_login(client):
    assert client.get("/account/profile").status_code == 302
    assert client.get("/account/settings").status_code == 302


def test_profile_page_renders_for_authenticated_user(client):
    _create_session_user(client)

    response = client.get("/account/profile")

    assert response.status_code == 200
    assert b"Profile" in response.data
    assert b"Save profile" in response.data


def test_settings_page_renders_for_authenticated_user(client):
    _create_session_user(client, email="settings@example.com")

    response = client.get("/account/settings")

    assert response.status_code == 200
    assert b"Settings" in response.data
    assert b"Email notifications" in response.data
