import os
import uuid
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.base_path = settings.UPLOAD_DIR
        
    def save_file(self, file_data: bytes, folder: str, extension: str) -> str:
        full_dir = os.path.join(self.base_path, folder)
        os.makedirs(full_dir, exist_ok=True)
        
        file_name = f"{uuid.uuid4().hex}.{extension}"
        file_path = os.path.join(full_dir, file_name)
        
        with open(file_path, "wb") as f:
            f.write(file_data)
            
        return os.path.relpath(file_path, self.base_path)

storage_service = StorageService()