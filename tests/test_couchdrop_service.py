from io import BytesIO
from types import SimpleNamespace

from werkzeug.datastructures import FileStorage

from app.services.couchdrop import CouchdropService


class DummyResponse:
    def __init__(self, status_code=201, text=""):
        self.status_code = status_code
        self.text = text


def test_upload_driver_paperwork_rewinds_stream_before_read(monkeypatch):
    monkeypatch.setenv("COUCHDROP_TOKEN", "test-token")
    CouchdropService._validated_paths.clear()

    upload_payloads = []

    def fake_get(url, headers=None, params=None):
        return DummyResponse(200)

    def fake_post(url, headers=None, params=None, data=None):
        if "file/upload" in url:
            upload_payloads.append(data)
        return DummyResponse(201)

    monkeypatch.setattr("app.services.couchdrop.requests.get", fake_get)
    monkeypatch.setattr("app.services.couchdrop.requests.post", fake_post)

    user = SimpleNamespace(first_name="Test", last_name="Driver")
    file_storage = FileStorage(stream=BytesIO(b"important-pdf-bytes"), filename="pod.pdf")

    # Simulate earlier logic consuming the stream before service upload.
    _ = file_storage.read()

    result = CouchdropService.upload_driver_paperwork(user, file_storage)

    assert result.endswith("/pod.pdf")
    assert upload_payloads == [b"important-pdf-bytes"]


def test_ensure_couchdrop_path_uses_cache(monkeypatch):
    CouchdropService._validated_paths.clear()
    get_calls = []

    def fake_get(url, headers=None, params=None):
        get_calls.append(params["path"])
        return DummyResponse(200)

    monkeypatch.setattr("app.services.couchdrop.requests.get", fake_get)

    assert CouchdropService._ensure_couchdrop_path_exists("token", "/Paperwork/Alice/2026-03-05") is True
    assert CouchdropService._ensure_couchdrop_path_exists("token", "/Paperwork/Alice/2026-03-05") is True

    assert get_calls == ["/Paperwork", "/Paperwork/Alice", "/Paperwork/Alice/2026-03-05"]


def test_upload_driver_paperwork_rejects_empty_payload(monkeypatch):
    monkeypatch.setenv("COUCHDROP_TOKEN", "test-token")

    post_calls = []

    def fake_post(url, headers=None, params=None, data=None):
        post_calls.append((url, data))
        return DummyResponse(201)

    monkeypatch.setattr("app.services.couchdrop.requests.post", fake_post)

    user = SimpleNamespace(first_name="Test", last_name="Driver")
    file_storage = FileStorage(stream=BytesIO(b""), filename="pod.pdf")

    result = CouchdropService.upload_driver_paperwork(user, file_storage)

    assert result is False
    assert post_calls == []
