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

    sent_payloads = []

    def fake_get(url, headers=None, params=None):
        return DummyResponse(200)

    monkeypatch.setattr("app.services.couchdrop.requests.get", lambda *args, **kwargs: DummyResponse(200))

    def fake_post(url, headers=None, params=None, data=None, files=None):
        if url.endswith("/file/upload"):
            sent_payloads.append(data)
        return DummyResponse(201)

    monkeypatch.setattr("app.services.couchdrop.requests.get", fake_get)
    monkeypatch.setattr("app.services.couchdrop.requests.post", fake_post)

    user = SimpleNamespace(first_name="Test", last_name="Driver")
    file_storage = FileStorage(stream=BytesIO(b"important-pdf-bytes"), filename="pod.pdf")

    _ = file_storage.read()

    result = CouchdropService.upload_driver_paperwork(user, file_storage)

    assert result.endswith("/pod.pdf")
    assert len(sent_payloads) == 1
    assert sent_payloads[0] == b"important-pdf-bytes"


def test_upload_driver_paperwork_uses_octet_stream_body_upload(monkeypatch):
    monkeypatch.setenv("COUCHDROP_TOKEN", "test-token")
    CouchdropService._validated_paths.clear()

    captured_requests = []

    monkeypatch.setattr("app.services.couchdrop.requests.get", lambda *args, **kwargs: DummyResponse(200))

    def fake_post(url, headers=None, params=None, data=None, files=None):
        if url.endswith("/file/upload"):
            captured_requests.append({"headers": headers, "params": params, "data": data, "files": files})
        return DummyResponse(201)

    monkeypatch.setattr("app.services.couchdrop.requests.post", fake_post)

    user = SimpleNamespace(first_name="Test", last_name="Driver")
    upload = FileStorage(stream=BytesIO(b"multipart-bytes"), filename="pod.pdf", content_type="application/pdf")

    result = CouchdropService.upload_driver_paperwork(user, upload)

    assert result.endswith("/pod.pdf")
    assert len(captured_requests) == 1
    assert captured_requests[0]["params"]["path"].endswith("/pod.pdf")
    assert captured_requests[0]["data"] == b"multipart-bytes"
    assert captured_requests[0]["files"] is None
    assert captured_requests[0]["headers"]["Content-Type"] == "application/octet-stream"


def test_upload_driver_paperwork_rejects_empty_payload(monkeypatch):
    monkeypatch.setenv("COUCHDROP_TOKEN", "test-token")

    monkeypatch.setattr("app.services.couchdrop.requests.get", lambda *args, **kwargs: DummyResponse(200))
    monkeypatch.setattr("app.services.couchdrop.requests.post", lambda *args, **kwargs: DummyResponse(201))

    user = SimpleNamespace(first_name="Test", last_name="Driver")
    empty_file = FileStorage(stream=BytesIO(b""), filename="pod.pdf")

    assert CouchdropService.upload_driver_paperwork(user, empty_file) is False


def test_base_url_accepts_full_upload_endpoint(monkeypatch):
    monkeypatch.setenv("COUCHDROP_BASE_URL", "https://fileio.couchdrop.io/file/upload")
    assert CouchdropService._api_url("/file/mkdir") == "https://fileio.couchdrop.io/file/mkdir"


def test_mkdir_404_falls_back_to_upload_attempt(monkeypatch):
    monkeypatch.setenv("COUCHDROP_TOKEN", "test-token")
    monkeypatch.setenv("COUCHDROP_BASE_URL", "https://fileio.couchdrop.io/file/upload")
    CouchdropService._validated_paths.clear()

    def fake_get(url, headers=None, params=None):
        return DummyResponse(404)

    calls = []

    def fake_post(url, headers=None, params=None, data=None, files=None):
        calls.append(url)
        if url.endswith("/file/mkdir"):
            return DummyResponse(404, "not found")
        if url.endswith("/file/upload"):
            return DummyResponse(201)
        return DummyResponse(201)

    monkeypatch.setattr("app.services.couchdrop.requests.get", fake_get)
    monkeypatch.setattr("app.services.couchdrop.requests.post", fake_post)

    user = SimpleNamespace(first_name="Test", last_name="Driver")
    upload = FileStorage(stream=BytesIO(b"bytes"), filename="pod.pdf")

    result = CouchdropService.upload_driver_paperwork(user, upload)

    assert result.endswith("/pod.pdf")
    assert any(url.endswith("/file/mkdir") for url in calls)
    assert any(url.endswith("/file/upload") for url in calls)


def test_upload_uses_legacy_endpoint_when_file_upload_returns_404(monkeypatch):
    monkeypatch.setenv("COUCHDROP_TOKEN", "test-token")
    monkeypatch.setenv("COUCHDROP_BASE_URL", "https://fileio.couchdrop.io")
    CouchdropService._validated_paths.clear()

    monkeypatch.setattr("app.services.couchdrop.requests.get", lambda *args, **kwargs: DummyResponse(200))

    calls = []

    def fake_post(url, headers=None, params=None, data=None, files=None):
        calls.append(url)
        if url.endswith("/file/upload"):
            return DummyResponse(404, "not found")
        if url.endswith("/upload"):
            return DummyResponse(201)
        return DummyResponse(201)

    monkeypatch.setattr("app.services.couchdrop.requests.post", fake_post)

    user = SimpleNamespace(first_name="Test", last_name="Driver")
    upload = FileStorage(stream=BytesIO(b"bytes"), filename="pod.pdf")

    result = CouchdropService.upload_driver_paperwork(user, upload)

    assert result.endswith("/pod.pdf")
    assert any(url.endswith("/file/upload") for url in calls)
    assert any(url.endswith("/upload") for url in calls)


def test_upload_fails_when_remote_stat_reports_zero_bytes(monkeypatch):
    monkeypatch.setenv("COUCHDROP_TOKEN", "test-token")
    monkeypatch.setenv("COUCHDROP_BASE_URL", "https://fileio.couchdrop.io")
    CouchdropService._validated_paths.clear()

    def fake_get(url, headers=None, params=None):
        if url.endswith("/file/stat") and params and params.get("path", "").endswith("/pod.pdf"):
            class JsonResponse(DummyResponse):
                def json(self):
                    return {"size": 0}

            return JsonResponse(200)

        return DummyResponse(200)

    monkeypatch.setattr("app.services.couchdrop.requests.get", fake_get)
    monkeypatch.setattr("app.services.couchdrop.requests.post", lambda *args, **kwargs: DummyResponse(201))

    user = SimpleNamespace(first_name="Test", last_name="Driver")
    upload = FileStorage(stream=BytesIO(b"bytes"), filename="pod.pdf")

    assert CouchdropService.upload_driver_paperwork(user, upload) is False


def test_upload_succeeds_when_remote_stat_size_is_positive(monkeypatch):
    monkeypatch.setenv("COUCHDROP_TOKEN", "test-token")
    monkeypatch.setenv("COUCHDROP_BASE_URL", "https://fileio.couchdrop.io")
    CouchdropService._validated_paths.clear()

    def fake_get(url, headers=None, params=None):
        if url.endswith("/file/stat") and params and params.get("path", "").endswith("/pod.pdf"):
            class JsonResponse(DummyResponse):
                def json(self):
                    return {"additional_info": {"size": 42}}

            return JsonResponse(200)

        return DummyResponse(200)

    monkeypatch.setattr("app.services.couchdrop.requests.get", fake_get)
    monkeypatch.setattr("app.services.couchdrop.requests.post", lambda *args, **kwargs: DummyResponse(201))

    user = SimpleNamespace(first_name="Test", last_name="Driver")
    upload = FileStorage(stream=BytesIO(b"bytes"), filename="pod.pdf")

    result = CouchdropService.upload_driver_paperwork(user, upload)
    assert result.endswith("/pod.pdf")
