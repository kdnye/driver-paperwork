import logging
import os
from datetime import datetime

from werkzeug.utils import secure_filename


class VolumeStorageService:
    # The path where the Google Cloud Storage bucket is mounted via Cloud Run
    MOUNT_PATH = "/driver_paperwork"

    @staticmethod
    def upload_driver_paperwork(user, file_storage):
        if not file_storage or not file_storage.filename:
            logging.error("Volume upload aborted: empty file payload")
            return False

        driver_name = f"{user.first_name}_{user.last_name}".replace(" ", "_")
        date_str = datetime.now().strftime("%Y-%m-%d")

        # Secure the filename to prevent directory traversal
        safe_filename = secure_filename(file_storage.filename)

        # Construct the destination folder path
        # E.g., /driver_paperwork/Paperwork/David_Alexander/2026-03-05
        folder_path = os.path.join(VolumeStorageService.MOUNT_PATH, "Paperwork", driver_name, date_str)
        file_path = os.path.join(folder_path, safe_filename)

        try:
            # Ensure the directory exists.
            # Cloud Run volume mounts (GCSFuse) support os.makedirs
            os.makedirs(folder_path, exist_ok=True)

            # Reset stream pointer to ensure the full file is saved
            if hasattr(file_storage, "stream") and hasattr(file_storage.stream, "seek"):
                file_storage.stream.seek(0)

            # Save the file directly to the mounted volume
            file_storage.save(file_path)

            logging.info("Successfully saved file to mounted volume: %s", file_path)

            # Return the file path so the route knows it succeeded
            return file_path

        except Exception as exc:
            logging.error(
                "Volume Storage Error: Failed to save %s. Exception: %s",
                file_path,
                str(exc),
            )
            return False
