import logging
import os
from io import BytesIO
from datetime import datetime

import requests


def _prepare_upload_payload(file_storage):
    """Return a rewound file-like payload and byte count for multipart upload."""
    stream = getattr(file_storage, "stream", None) or file_storage

    if hasattr(stream, "seek"):
        try:
            stream.seek(0)
        except Exception:
            pass

    byte_count = None
    if hasattr(stream, "tell") and hasattr(stream, "seek"):
        try:
            current = stream.tell()
            stream.seek(0, os.SEEK_END)
            byte_count = stream.tell()
            stream.seek(0)
            if current and current != 0:
                stream.seek(0)
        except Exception:
            byte_count = None

    if byte_count is None:
        try:
            raw_bytes = stream.read() if hasattr(stream, "read") else b""
        except Exception:
            raw_bytes = b""

        if isinstance(raw_bytes, str):
            raw_bytes = raw_bytes.encode("utf-8")

        stream = BytesIO(raw_bytes or b"")
        stream.seek(0)
        byte_count = len(raw_bytes or b"")

    return stream, byte_count

class CouchdropService:
    _validated_paths = set()

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
        headers = {"token": token}

        for segment in segments:
            current_path = f"{current_path}/{segment}" if current_path else f"/{segment}"

            if current_path in cls._validated_paths:
                continue

            check_response = requests.get(
                "https://fileio.couchdrop.io/file/stat",
                headers=headers,
                params={"path": current_path}
            )

            if check_response.status_code == 200:
                cls._validated_paths.add(current_path)
                continue

            create_response = requests.post(
                "https://fileio.couchdrop.io/file/mkdir",
                headers=headers,
                params={"path": current_path}
            )

            if create_response.status_code not in (200, 201):
                logging.error(
                    "Failed to create Couchdrop directory [%s]: %s %s",
                    current_path,
                    create_response.status_code,
                    create_response.text,
                )
                return False

            cls._validated_paths.add(current_path)

        cls._validated_paths.add(normalized_path)
        return True

    @staticmethod
    def upload_driver_paperwork(user, file_storage):
        raw_token = os.getenv("COUCHDROP_TOKEN")
        if not raw_token:
            raise ValueError("CRITICAL: COUCHDROP_TOKEN environment variable is missing or empty.")
            
        token = raw_token.strip()
        
        # 1. Format names safely with underscores to prevent folder name truncation
        driver_name = f"{user.first_name}_{user.last_name}".replace(" ", "_")
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        folder_path = f"/Paperwork/{driver_name}/{date_str}"
        remote_path = f"{folder_path}/{file_storage.filename}"
        
        headers = {"token": token}
        
        payload_stream, payload_size = _prepare_upload_payload(file_storage)
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
                "https://fileio.couchdrop.io/file/upload",
                headers=headers,
                params={"path": remote_path},
                files={
                    "file": (
                        file_storage.filename,
                        payload_stream,
                        getattr(file_storage, "content_type", None) or "application/octet-stream",
                    )
                },
            )
            
            if response.status_code not in (200, 201):
                logging.error(f"Couchdrop Upload Failed [{response.status_code}]: {response.text}")
                return False
                
            return remote_path
            
        except Exception as e:
            logging.error(f"Couchdrop Connection Error: {str(e)}")
            return False
