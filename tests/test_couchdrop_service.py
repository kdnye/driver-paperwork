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

    sent_payloads = []

    def fake_post(url, headers=None, params=None, data=None):
        sent_payloads.append(data)
        return DummyResponse(201)

    monkeypatch.setattr("app.services.couchdrop.requests.post", fake_post)

    user = SimpleNamespace(first_name="Test", last_name="Driver")
    file_storage = FileStorage(stream=BytesIO(b"important-pdf-bytes"), filename="pod.pdf")

    # Simulate earlier logic consuming the stream before service upload.
    _ = file_storage.read()

    result = CouchdropService.upload_driver_paperwork(user, file_storage)

    assert result is True
    assert sent_payloads == [b"important-pdf-bytes"]
