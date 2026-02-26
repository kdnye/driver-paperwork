import os
import requests
import logging
import base64
from datetime import datetime

class CouchdropService:
    @staticmethod
    def upload_driver_paperwork(user, file_storage):
        token = os.getenv("COUCHDROP_TOKEN")
        driver_name = f"{user.first_name} {user.last_name}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        remote_path = f"/Paperwork/{driver_name}/{date_str}/{file_storage.filename}"
        
        # Format the token correctly for Couchdrop's FileIO Basic Auth
        # It expects "base64(token:)" where the password side is empty.
        auth_str = f"{token}:"
        b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        
        headers = {
            "Authorization": f"Basic {b64_auth}",
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
