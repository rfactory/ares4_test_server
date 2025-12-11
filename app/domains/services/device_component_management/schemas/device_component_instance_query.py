# schemas/device_component_instance_query.py

from pydantic import BaseModel, ConfigDict
from typing import Optional

# --- Nested Schema for SupportedComponent ---
class SupportedComponentInfo(BaseModel):
    """부품 인스턴스 조회 시 반환될 최소한의 부품 정보"""
    id: int
    name: str
    version: str
    manufacturer: str

    model_config = ConfigDict(from_attributes=True)

# --- Main Schema for DeviceComponentInstance ---
class DeviceComponentInstanceRead(BaseModel):
    """장치에 연결된 부품 인스턴스 조회 시 반환될 모델"""
    id: int
    instance_name: str
    description: Optional[str] = None
    supported_component: SupportedComponentInfo

    model_config = ConfigDict(from_attributes=True)
