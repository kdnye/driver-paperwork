import os
import requests
from datetime import datetime
from flask import current_app

class CouchdropService:
    @staticmethod
    def upload_driver_paperwork(user, file_storage):
        token = os.getenv("COUCHDROP_TOKEN")
        # Structure: /Paperwork/{Driver Name}/{Date}/
        driver_name = f"{user.first_name} {user.last_name}"
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # The Couchdrop path maps to the 'Driver paperwork' connection folder
        remote_path = f"/Paperwork/{driver_name}/{date_str}/{file_storage.filename}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        files = {
            'file': (file_storage.filename, file_storage.stream, file_storage.content_type)
        }
        
        # Couchdrop V2 Upload Endpoint
        response = requests.post(
            f"{os.getenv('COUCHDROP_BASE_URL')}/upload",
            headers=headers,
            data={"path": remote_path},
            files=files
        )
        
        return response.status_code == 200 or response.status_code == 201
