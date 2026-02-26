import os
import requests
import logging
from datetime import datetime

class CouchdropService:
    @staticmethod
    def upload_driver_paperwork(user, file_storage):
        raw_token = os.getenv("COUCHDROP_TOKEN")
        if not raw_token:
            raise ValueError("CRITICAL: COUCHDROP_TOKEN environment variable is missing or empty.")
            
        token = raw_token.strip()
        
        driver_name = f"{user.first_name} {user.last_name}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Target folder structure
        folder_path = f"/Paperwork/{driver_name}/{date_str}"
        remote_path = f"{folder_path}/{file_storage.filename}"
        
        # 1. Progressively create directories to prevent "Parent folder not found" 404s
        parts = [p for p in folder_path.split("/") if p]
        current_dir = ""
        for part in parts:
            current_dir += f"/{part}"
            try:
                requests.post(
                    "https://fileio.couchdrop.io/file/mkdir",
                    headers={"token": token},
                    params={"path": current_dir}
                )
                # Responses are ignored here. If the folder already exists, it throws a non-200 
                # status which is expected and perfectly fine to bypass.
            except Exception as e:
                logging.warning(f"Couchdrop mkdir failed for {current_dir}: {str(e)}")

        # 2. Upload the raw file bytes into the newly verified folder tree
        headers = {
            "token": token,
            "Content-Type": "application/octet-stream"
        }
        
        params = {
            "path": remote_path
        }
        
        file_bytes = file_storage.read()
        
        try:
            response = requests.post(
                "https://fileio.couchdrop.io/file/upload",
                headers=headers,
                params=params,
                data=file_bytes
            )
            
            if response.status_code not in (200, 201):
                logging.error(f"Couchdrop Upload Failed [{response.status_code}]: {response.text}")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Couchdrop Connection Error: {str(e)}")
            return False
