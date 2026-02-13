from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PinMappingRead(BaseModel):
    """UI 혹은 기기에게 배선 정보를 응답할 때 사용"""
    id: int
    pin_name: str
    pin_number: int
    pin_mode: Optional[str]
    device_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True