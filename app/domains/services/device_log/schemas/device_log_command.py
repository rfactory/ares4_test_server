from pydantic import BaseModel
from typing import Optional, Dict, Any

class DeviceLogCreate(BaseModel):
    device_id: int
    log_level: str = 'INFO'
    description: str
    metadata_json: Optional[Dict[str, Any]] = None
