import os
import requests
import logging
from datetime import datetime

class CouchdropService:
    @staticmethod
    def upload_driver_paperwork(user, file_storage):
        # 1. Force a loud crash if the secret is missing or empty.
        raw_token = os.getenv("COUCHDROP_TOKEN")
        if not raw_token:
            raise ValueError("CRITICAL: COUCHDROP_TOKEN environment variable is missing or empty. Check Secret Manager wiring.")
            
        token = raw_token.strip()
        
        driver_name = f"{user.first_name} {user.last_name}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        remote_path = f"/Paperwork/{driver_name}/{date_str}/{file_storage.filename}"
        
        # 2. Use the exact header format from the Couchdrop documentation
        headers = {
            "token": token,
            "Content-Type": "application/octet-stream"
        }
        
        # 3. Path goes in query params for fileio
        params = {
            "path": remote_path
        }
        
        file_bytes = file_storage.read()
        
        try:
            # 4. Use the correct fileio subdomain
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
