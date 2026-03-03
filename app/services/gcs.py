import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class GCSService:
    """Uploads bytes to a remote file endpoint backed by GCS."""

    def __init__(self) -> None:
        self._token = (os.getenv("GCS_TOKEN") or "").strip()
        self._bucket = (os.getenv("GCS_BUCKET") or "").strip()
        self._upload_url = os.getenv("GCS_UPLOAD_URL", "https://fileio.couchdrop.io/file/upload")
        self._mkdir_url = os.getenv("GCS_MKDIR_URL", "https://fileio.couchdrop.io/file/mkdir")
        self._uri_prefix = (os.getenv("GCS_URI_PREFIX") or f"gs://{self._bucket}").rstrip("/")

    def upload_file(self, file_obj, destination_dir: str, filename: str) -> Optional[str]:
        """Upload a file-like object and return its URI when successful."""
        if not self._token:
            logger.error("Missing GCS token; cannot upload file")
            return None

        clean_dir = "/" + destination_dir.strip("/") if destination_dir else ""
        remote_path = f"{clean_dir}/{filename}" if clean_dir else f"/{filename}"

        if not self._ensure_destination_path(clean_dir):
            return None

        headers = {
            "token": self._token,
            "Content-Type": "application/octet-stream",
        }

        # Reset cursor immediately before reading so previously-read streams upload correctly.
        file_obj.seek(0)
        file_bytes = file_obj.read()

        try:
            response = requests.post(
                self._upload_url,
                headers=headers,
                params={"path": remote_path},
                data=file_bytes,
            )
        except requests.RequestException:
            logger.exception("GCS upload request failed", extra={"path": remote_path})
            return None

        if response.status_code not in (200, 201):
            logger.error(
                "GCS upload failed",
                extra={
                    "status_code": response.status_code,
                    "response_body": response.text,
                    "path": remote_path,
                },
            )
            return None

        return f"{self._uri_prefix}{remote_path}"

    def _ensure_destination_path(self, destination_dir: str) -> bool:
        """Create destination directories one-by-one if they do not already exist."""
        if not destination_dir:
            return True

        headers = {"token": self._token}
        current_path = ""

        for segment in [part for part in destination_dir.split("/") if part]:
            current_path = f"{current_path}/{segment}"
            try:
                response = requests.post(
                    self._mkdir_url,
                    headers=headers,
                    params={"path": current_path},
                )
            except requests.RequestException:
                logger.exception("Failed to ensure destination segment", extra={"path": current_path})
                return False

            if response.status_code not in (200, 201, 409):
                logger.error(
                    "Failed to create destination segment",
                    extra={
                        "status_code": response.status_code,
                        "response_body": response.text,
                        "path": current_path,
                    },
                )
                return False

        return True
