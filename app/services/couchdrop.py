import os
import requests
import logging
from datetime import datetime


def _read_upload_bytes(file_storage):
    """Return upload bytes from FileStorage after rewinding when possible."""
    stream = getattr(file_storage, "stream", file_storage)

    if hasattr(stream, "seek"):
        stream.seek(0)

    file_bytes = stream.read()
    if isinstance(file_bytes, str):
        file_bytes = file_bytes.encode("utf-8")

    return file_bytes or b""

class CouchdropService:
    @staticmethod
    def _ensure_couchdrop_path_exists(token, destination_path):
        normalized_path = destination_path.strip()
        if not normalized_path:
            raise ValueError("destination_path cannot be empty.")

        segments = [segment for segment in normalized_path.strip("/").split("/") if segment]
        if not segments:
            raise ValueError("destination_path must include at least one folder segment.")

        current_path = ""
        headers = {"token": token}

        for segment in segments:
            current_path = f"{current_path}/{segment}" if current_path else f"/{segment}"

            check_response = requests.get(
                "https://api.couchdrop.io/manage/fileprops",
                headers=headers,
                params={"path": current_path}
            )

            if check_response.status_code == 200:
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
        
        headers = {
            "token": token,
            "Content-Type": "application/octet-stream"
        }
        
        # Reset stream position in case validation/routes already consumed bytes.
        # Read once into bytes so the request body is deterministic.
        file_bytes = _read_upload_bytes(file_storage)
        if not file_bytes:
            logging.error("Couchdrop upload aborted: empty file payload", extra={"path": remote_path})
            return False
        
        try:
            if not CouchdropService._ensure_couchdrop_path_exists(token, folder_path):
                return False

            response = requests.post(
                "https://fileio.couchdrop.io/file/upload",
                headers=headers,
                params={"path": remote_path},
                data=file_bytes
            )
            
            if response.status_code not in (200, 201):
                logging.error(f"Couchdrop Upload Failed [{response.status_code}]: {response.text}")
                return False
                
            return remote_path
            
        except Exception as e:
            logging.error(f"Couchdrop Connection Error: {str(e)}")
            return False
