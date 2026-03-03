from pathlib import Path


def test_login_stores_user_identity_in_session(client, create_user):
    user_id = create_user("login@example.com", employee_approved=True)

    response = client.post(
        "/auth/login",
        data={"email": "login@example.com", "password": "does-not-matter"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/post-login")

    with client.session_transaction() as sess:
        assert sess["current_user_id"] == user_id


def test_login_normalizes_email_input_before_lookup(client, create_user):
    user_id = create_user("normalize@example.com", employee_approved=True)

    response = client.post(
        "/auth/login",
        data={"email": "  NoRMalize@Example.com  "},
        follow_redirects=False,
    )

    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert sess["current_user_id"] == user_id


def test_login_rejects_unknown_email(client):
    response = client.post("/auth/login", data={"email": "missing@example.com"})

    assert response.status_code == 401


def test_login_rejects_blank_email(client):
    response = client.post("/auth/login", data={"email": "   "})

    assert response.status_code == 401


def test_login_template_loads_global_theme_script(client):
    response = client.get("/auth/login")

    assert response.status_code == 200
    assert b"/static/js/theme.js" in response.data


def test_base_template_references_theme_asset():
    base_template = (Path(__file__).resolve().parents[1] / "templates" / "base.html").read_text()

    assert "url_for('static', filename='js/theme.js')" in base_template


def test_root_redirects_to_login_when_not_authenticated(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_root_redirects_to_upload_when_authenticated(app, client):
    from werkzeug.security import generate_password_hash

    from app import db
    from models import User

    with app.app_context():
        user = User(
            email="root-redirect@example.com",
            password_hash=generate_password_hash("test-password"),
            employee_approved=True,
            role="EMPLOYEE",
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess["current_user_id"] = user_id

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/upload")
