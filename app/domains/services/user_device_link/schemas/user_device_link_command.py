# --- Command-related Schemas ---
from pydantic import BaseModel
from typing import Optional

class UserDeviceLinkBase(BaseModel):
    user_id: int
    device_id: int
    role: str = "viewer" # e.g., owner, viewer
    nickname: Optional[str] = None

class UserDeviceLinkCreate(UserDeviceLinkBase):
    pass

class UserDeviceLinkUpdate(BaseModel):
    role: Optional[str] = None
    nickname: Optional[str] = None
