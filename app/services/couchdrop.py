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
        
        remote_path = f"/Paperwork/{driver_name}/{date_str}/{file_storage.filename}"
        
        # Only standard content headers here; NO auth headers
        headers = {
            "Content-Type": "application/octet-stream"
        }
        
        # FIX: The FileIO endpoint requires the token to be passed as a query string parameter
        params = {
            "path": remote_path,
            "token": token  # Add token to the URL (?path=...&token=...)
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
