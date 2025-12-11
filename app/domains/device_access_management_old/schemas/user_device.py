from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

# --- UserDevice Schemas (for linking Users to Devices) ---
class UserDeviceBase(BaseModel):
    user_id: int
    device_id: int
    role: str = "viewer" # e.g., owner, viewer
    nickname: Optional[str] = None

class UserDeviceCreate(UserDeviceBase):
    pass

class UserDevice(UserDeviceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
