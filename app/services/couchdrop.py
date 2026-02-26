import os
import requests
import logging
from datetime import datetime

class CouchdropService:
    @staticmethod
    def upload_driver_paperwork(user, file_storage):
        token = os.getenv("COUCHDROP_TOKEN")
        
        # Couchdrop usually requires you to send to a specific URL or use basic auth 
        # with your username/token. 
        driver_name = f"{user.first_name} {user.last_name}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Determine the destination path inside Couchdrop
        # Make sure the path starts with a slash
        remote_path = f"/Paperwork/{driver_name}/{date_str}/{file_storage.filename}"
        
        # For Couchdrop v3 uploads, standard Basic Auth is required
        # Note: Some accounts use an email instead of "token" for the username.
        # Check your Couchdrop account settings if "token" doesn't work.
        auth = ("token", token) 
        
        # Set Content-Type so it doesn't try to format it as a multipart form
        headers = {
            "Content-Type": "application/octet-stream"
        }
        
        # The path goes in the query string
        params = {
            "path": remote_path
        }
        
        file_bytes = file_storage.read()
        
        try:
            # Using the v3 endpoint which is standard for HTTP POST uploads
            response = requests.post(
                "https://api.couchdrop.io/v3/upload",
                auth=auth,
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
