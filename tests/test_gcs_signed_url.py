from app.services.gcs import GCSService


def test_generate_signed_url_uses_public_service_url_fallback(monkeypatch):
    monkeypatch.setenv("PUBLIC_SERVICE_URL", "https://public.example.com/assets")
    monkeypatch.delenv("GCS_SIGN_URL_ENDPOINT", raising=False)

    service = GCSService()

    assert service.generate_signed_url("pod/POD-100-signature.png") == (
        "https://public.example.com/assets/pod/POD-100-signature.png"
    )


def test_generate_signed_url_strips_gs_bucket_prefix(monkeypatch):
    monkeypatch.setenv("PUBLIC_SERVICE_URL", "https://public.example.com/assets")
    monkeypatch.setenv("GCS_BUCKET", "driver-paperwork")
    monkeypatch.delenv("GCS_SIGN_URL_ENDPOINT", raising=False)

    service = GCSService()

    assert service.generate_signed_url("gs://driver-paperwork/pod/POD-101-picture.jpg") == (
        "https://public.example.com/assets/pod/POD-101-picture.jpg"
    )
