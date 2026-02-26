import os
import requests
import logging
from datetime import datetime

class CouchdropService:
    @staticmethod
    def upload_driver_paperwork(user, file_storage):
        raw_token = os.getenv("COUCHDROP_TOKEN")
        
        # 1. Proactive Debugging: Catch empty or missing secrets instantly
        if not raw_token or not raw_token.strip():
            logging.error("CRITICAL ERROR: COUCHDROP_TOKEN is missing or empty in the environment!")
            return False
            
        # 2. Strip hidden newlines injected by Google Secret Manager
        token = raw_token.strip()
        
        driver_name = f"{user.first_name} {user.last_name}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        remote_path = f"/Paperwork/{driver_name}/{date_str}/{file_storage.filename}"
        
        # 3. Couchdrop FileIO officially expects the header named exactly "token"
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
