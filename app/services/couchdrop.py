import os
import requests
import logging
from datetime import datetime

class CouchdropService:
    @staticmethod
    def upload_driver_paperwork(user, file_storage):
        token = os.getenv("COUCHDROP_TOKEN")
        driver_name = f"{user.first_name} {user.last_name}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Determine the destination path inside Couchdrop
        remote_path = f"/Paperwork/{driver_name}/{date_str}/{file_storage.filename}"
        
        # FIX: Change 'Authorization' to the custom 'token' header required by FileIO
        headers = {
            "token": token,  # <--- This must be named exactly "token"
            "Content-Type": "application/octet-stream"
        }
        
        # Couchdrop requires the path to be a query parameter
        params = {
            "path": remote_path
        }
        
        # Read the raw binary from the uploaded file
        file_bytes = file_storage.read()
        
        try:
            # Use the dedicated FileIO endpoint for binary uploads
            response = requests.post(
                "https://fileio.couchdrop.io/file/upload",
                headers=headers,
                params=params,
                data=file_bytes
            )
            
            # Log exact failure reasons to Cloud Run if it gets rejected
            if response.status_code not in (200, 201):
                logging.error(f"Couchdrop Upload Failed [{response.status_code}]: {response.text}")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Couchdrop Connection Error: {str(e)}")
            return False
