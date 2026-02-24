from pathlib import Path

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


def _create_user(email: str, employee_approved: bool, role: Role = Role.EMPLOYEE) -> int:
    user = User(email=email, role=role, employee_approved=employee_approved)
    db.session.add(user)
    db.session.commit()
    return user.id


def test_approved_user_can_access_protected_routes(client, app):
    with app.app_context():
        user_id = _create_user("approved@example.com", employee_approved=True)

    with client.session_transaction() as sess:
        sess["current_user_id"] = user_id

    response = client.get("/auth/internal/dashboard")

    assert response.status_code == 200
    assert response.get_json() == {"dashboard": "internal-tools"}


def test_unapproved_user_is_redirected_to_pending_page(client, app):
    with app.app_context():
        user_id = _create_user("pending@example.com", employee_approved=False)

    with client.session_transaction() as sess:
        sess["current_user_id"] = user_id

    response = client.get("/auth/internal/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/pending-approval")

    pending_page = client.get(response.headers["Location"])
    assert pending_page.status_code == 403
    assert b"Approval Pending" in pending_page.data


def test_unapproved_user_gets_403_on_api_guard(client, app):
    with app.app_context():
        user_id = _create_user("api-pending@example.com", employee_approved=False)

    with client.session_transaction() as sess:
        sess["current_user_id"] = user_id

    response = client.get("/auth/gate/internal_dashboard/view")

    assert response.status_code == 403
    assert response.get_json() == {"error": "Employee approval is required."}


def test_employee_denied_finance_action(client, app):
    with app.app_context():
        user_id = _create_user("employee@example.com", employee_approved=True, role=Role.EMPLOYEE)

    with client.session_transaction() as sess:
        sess["current_user_id"] = user_id

    response = client.get("/auth/gate/finance_ledger/approve")

    assert response.status_code == 403
    assert response.get_json()["error"] == "Access denied."
    assert "ACCESS_DENIED insufficient_role" in response.get_json()["detail"]
    assert "required=FINANCE" in response.get_json()["detail"]


def test_finance_can_approve_finance_action(client, app):
    with app.app_context():
        user_id = _create_user("finance@example.com", employee_approved=True, role=Role.FINANCE)

    with client.session_transaction() as sess:
        sess["current_user_id"] = user_id

    response = client.get("/auth/gate/finance_ledger/approve")

    assert response.status_code == 200
    assert response.get_json() == {
        "resource": "finance_ledger",
        "action": "approve",
        "allowed": True,
    }


def test_supervisor_can_approve_team_action(client, app):
    with app.app_context():
        user_id = _create_user("supervisor@example.com", employee_approved=True, role=Role.SUPERVISOR)

    with client.session_transaction() as sess:
        sess["current_user_id"] = user_id

    response = client.get("/auth/gate/team_approvals/approve")

    assert response.status_code == 200
    assert response.get_json()["allowed"] is True


def test_unknown_policy_target_returns_403_with_audit_message(client, app):
    with app.app_context():
        user_id = _create_user("admin@example.com", employee_approved=True, role=Role.ADMIN)

    with client.session_transaction() as sess:
        sess["current_user_id"] = user_id

    response = client.get("/auth/gate/unknown_resource/delete")

    assert response.status_code == 403
    assert response.get_json()["error"] == "Access denied."
    assert "ACCESS_DENIED policy_missing" in response.get_json()["detail"]


def test_login_stores_user_identity_in_session(client, app):
    with app.app_context():
        user_id = _create_user("login@example.com", employee_approved=True)

    response = client.post(
        "/auth/login",
        data={"email": "login@example.com", "password": "does-not-matter"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/post-login")

    with client.session_transaction() as sess:
        assert sess["current_user_id"] == user_id


def test_login_template_loads_global_theme_script(client):
    response = client.get('/auth/login')

    assert response.status_code == 200
    assert b'/static/js/theme.js' in response.data


def test_base_template_references_theme_asset():
    base_template = (Path(__file__).resolve().parents[1] / 'templates' / 'base.html').read_text()

    assert "url_for('static', filename='js/theme.js')" in base_template
