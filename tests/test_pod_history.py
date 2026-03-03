from app import db
from models import PodSubmission, User


def _create_session_user(client, email="pod-history@example.com"):
    user = User(email=email, password_hash="x", employee_approved=True)
    db.session.add(user)
    db.session.commit()

    with client.session_transaction() as sess:
        sess["current_user_id"] = user.id

    return user


def test_submit_pod_records_picture_and_signature_links(client, monkeypatch):
    _create_session_user(client)

    monkeypatch.setattr(
        "app.blueprints.paperwork.routes.CouchdropService.upload_driver_paperwork",
        lambda *_args, **_kwargs: "/Paperwork/Driver/POD-7781-file.bin",
    )

    payload = {
        "pod_id": "POD-7781",
        "pod_picture_url": "https://cdn.example.com/pod/POD-7781-picture.jpg",
        "captured_signature_url": "https://cdn.example.com/pod/POD-7781-signature.png",
        "generated_files": [
            {
                "filename": "POD-7781-picture.jpg",
                "content_base64": "aGVsbG8=",
            },
            {
                "filename": "POD-7781-signature.png",
                "content_base64": "d29ybGQ=",
            },
        ],
    }

    response = client.post("/pod/submit", json=payload)

    assert response.status_code == 200

    saved = PodSubmission.query.filter_by(pod_reference="POD-7781").all()
    assert len(saved) == 2
    assert all(record.uploaded_file_uri for record in saved)

    with client.session_transaction() as sess:
        assert sess["pod_history"][0]["pod_reference"] == "POD-7781"
        assert sess["pod_history"][0]["pod_picture_url"].endswith("picture.jpg")
        assert sess["pod_history"][0]["captured_signature_url"].endswith("signature.png")


def test_submit_pod_rolls_back_when_upload_uri_is_missing(client, monkeypatch):
    _create_session_user(client, email="pod-rollback@example.com")

    monkeypatch.setattr(
        "app.blueprints.paperwork.routes.CouchdropService.upload_driver_paperwork",
        lambda *_args, **_kwargs: None,
    )

    payload = {
        "pod_id": "POD-ROLLBACK-1",
        "generated_files": [
            {
                "filename": "POD-ROLLBACK-1-picture.jpg",
                "content_base64": "aGVsbG8=",
            }
        ],
    }

    response = client.post("/pod/submit", json=payload)

    assert response.status_code == 422
    assert "rolled back" in response.get_json()["error"].lower()
    assert PodSubmission.query.filter_by(pod_reference="POD-ROLLBACK-1").count() == 0


def test_history_page_renders_pod_links(client):
    _create_session_user(client, email="pod-links@example.com")

    with client.session_transaction() as sess:
        sess["pod_history"] = [
            {
                "pod_reference": "POD-009",
                "pod_picture_url": "https://cdn.example.com/pod/POD-009-picture.jpg",
                "captured_signature_url": "https://cdn.example.com/pod/POD-009-signature.png",
            }
        ]

    response = client.get("/history")

    assert response.status_code == 200
    assert b"POD-009" in response.data
    assert b"POD Picture" in response.data
    assert b"Captured Signature" in response.data
    assert b"POD-009-picture.jpg" in response.data
    assert b"POD-009-signature.png" in response.data
