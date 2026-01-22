from typing import Optional
from pydantic import BaseModel

class PermissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_system_locked: bool
    ui_group: Optional[str]

    class Config:
        from_attributes = True
