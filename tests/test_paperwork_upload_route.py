from io import BytesIO

from app import db
from models import User


def _create_logged_in_user(client, email):
    user = User(
        email=email,
        password_hash="x",
        first_name="Test",
        last_name="Driver",
        employee_approved=True,
    )
    db.session.add(user)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["current_user_id"] = user.id


def test_upload_ajax_returns_422_when_service_upload_fails(client, monkeypatch):
    _create_logged_in_user(client, "driver@example.com")

    monkeypatch.setattr(
        "app.blueprints.paperwork.routes.CouchdropService.upload_driver_paperwork",
        lambda *_args, **_kwargs: False,
    )

    response = client.post(
        "/upload",
        data={"scans": (BytesIO(b"test-data"), "scan1.pdf")},
        headers={"Accept": "application/json"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 422
    assert response.get_json()["success_count"] == 0


def test_upload_ajax_returns_422_for_zero_byte_file_without_calling_service(client, monkeypatch):
    _create_logged_in_user(client, "driver2@example.com")

    called = {"value": False}

    def _fake_upload(*_args, **_kwargs):
        called["value"] = True
        return True

    monkeypatch.setattr(
        "app.blueprints.paperwork.routes.CouchdropService.upload_driver_paperwork",
        _fake_upload,
    )

    response = client.post(
        "/upload",
        data={"scans": (BytesIO(b""), "empty.pdf")},
        headers={"Accept": "application/json"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 422
    assert response.get_json()["success_count"] == 0
    assert called["value"] is False
