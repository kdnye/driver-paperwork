import logging
import os
from datetime import datetime
from urllib.parse import urlparse, urlunparse

import requests


def _prepare_upload_payload(file_storage):
    """Return upload bytes and byte count from the incoming file object."""
    stream = getattr(file_storage, "stream", None) or file_storage

    if hasattr(stream, "seek"):
        try:
            stream.seek(0)
        except Exception:
            pass

    try:
        raw_bytes = stream.read() if hasattr(stream, "read") else b""
    except Exception:
        raw_bytes = b""

    if isinstance(raw_bytes, str):
        raw_bytes = raw_bytes.encode("utf-8")

    if hasattr(stream, "seek"):
        try:
            stream.seek(0)
        except Exception:
            pass

    return raw_bytes or b"", len(raw_bytes or b"")


class CouchdropService:
    _validated_paths = set()

    @staticmethod
    def _service_base_url():
        """Resolve a stable Couchdrop API root URL.

        Accepts either a host base (e.g. https://fileio.couchdrop.io) or a full
        endpoint URL accidentally provided in COUCHDROP_BASE_URL
        (e.g. https://fileio.couchdrop.io/file/upload).
        """
        raw = (os.getenv("COUCHDROP_BASE_URL") or "https://fileio.couchdrop.io").strip()
        parsed = urlparse(raw)

        if not parsed.scheme or not parsed.netloc:
            return "https://fileio.couchdrop.io"

        clean_path = parsed.path.rstrip("/")
        for suffix in ("/file/upload", "/file/mkdir", "/file/stat"):
            if clean_path.endswith(suffix):
                clean_path = clean_path[: -len(suffix)]
                break

        return urlunparse((parsed.scheme, parsed.netloc, clean_path, "", "", "")).rstrip("/")

    @classmethod
    def _api_url(cls, path):
        return f"{cls._service_base_url()}/{path.lstrip('/')}"

    @classmethod
    def _ensure_couchdrop_path_exists(cls, token, destination_path):
        normalized_path = destination_path.strip()
        if not normalized_path:
            raise ValueError("destination_path cannot be empty.")

        if normalized_path in cls._validated_paths:
            return True

        segments = [segment for segment in normalized_path.strip("/").split("/") if segment]
        if not segments:
            raise ValueError("destination_path must include at least one folder segment.")

        current_path = ""
        headers = {"token": token, "Content-Type": "application/octet-stream"}

        for segment in segments:
            current_path = f"{current_path}/{segment}" if current_path else f"/{segment}"

            if current_path in cls._validated_paths:
                continue

            check_response = requests.get(
                cls._api_url("/file/stat"),
                headers=headers,
                params={"path": current_path},
            )

            if check_response.status_code == 200:
                cls._validated_paths.add(current_path)
                continue

            create_response = requests.post(
                cls._api_url("/file/mkdir"),
                headers=headers,
                params={"path": current_path},
            )

            if create_response.status_code in (200, 201, 409):
                cls._validated_paths.add(current_path)
                continue

            if create_response.status_code == 404:
                logging.warning(
                    "Couchdrop mkdir endpoint returned 404; continuing without directory pre-creation.",
                    extra={"path": current_path, "endpoint": cls._api_url('/file/mkdir')},
                )
                return True

            logging.error(
                "Failed to create Couchdrop directory [%s]: %s %s",
                current_path,
                create_response.status_code,
                create_response.text,
            )
            return False

        cls._validated_paths.add(normalized_path)
        return True

    @staticmethod
    def upload_driver_paperwork(user, file_storage):
        raw_token = os.getenv("COUCHDROP_TOKEN")
        if not raw_token:
            raise ValueError("CRITICAL: COUCHDROP_TOKEN environment variable is missing or empty.")

        token = raw_token.strip()

        driver_name = f"{user.first_name}_{user.last_name}".replace(" ", "_")
        date_str = datetime.now().strftime("%Y-%m-%d")

        folder_path = f"/Paperwork/{driver_name}/{date_str}"
        remote_path = f"{folder_path}/{file_storage.filename}"

        headers = {"token": token, "Content-Type": "application/octet-stream"}
        
        payload_bytes, payload_size = _prepare_upload_payload(file_storage)
        if payload_size <= 0:
            logging.error("Couchdrop upload aborted: empty file payload", extra={"path": remote_path})
            return False

        logging.info(
            "Couchdrop upload payload prepared",
            extra={"path": remote_path, "byte_count": payload_size},
        )

        try:
            if not CouchdropService._ensure_couchdrop_path_exists(token, folder_path):
                return False

            response = requests.post(
                CouchdropService._api_url("/file/upload"),
                headers=headers,
                params={"path": remote_path},
                data=payload_bytes,
            )

            if response.status_code not in (200, 201):
                logging.error(f"Couchdrop Upload Failed [{response.status_code}]: {response.text}")
                return False

            return remote_path

        except Exception as e:
            logging.error(f"Couchdrop Connection Error: {str(e)}")
            return False
