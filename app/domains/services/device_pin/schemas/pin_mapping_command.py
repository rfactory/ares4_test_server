from pydantic import BaseModel
from typing import Optional
from app.models.relationships.device_component_pin_mapping import PinStatusEnum

class PinMappingCreate(BaseModel):
    pin_name: str
    pin_number: int
    pin_mode: Optional[str] = "INPUT"
    device_id: int
    device_component_instance_id: Optional[int] = None
    status: PinStatusEnum = PinStatusEnum.ACTIVE

class PinMappingUpdate(BaseModel):
    pin_number: Optional[int] = None
    pin_mode: Optional[str] = None
    status: Optional[PinStatusEnum] = None