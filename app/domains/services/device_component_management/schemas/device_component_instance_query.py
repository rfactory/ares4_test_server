# schemas/device_component_instance_query.py

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

# --- Nested Schema for SupportedComponent ---
class SupportedComponentInfo(BaseModel):
    """부품 인스턴스 조회 시 반환될 최소한의 부품 정보"""
    id: int
    name: str = Field(validation_alias="display_name")
    version: str = Field(validation_alias="model_name")
    manufacturer: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# --- Main Schema for DeviceComponentInstance ---
class DeviceComponentInstanceRead(BaseModel):
    """장치에 연결된 부품 인스턴스 조회 시 반환될 모델"""
    id: int
    instance_name: str
    description: Optional[str] = None
    spatial_context: dict = Field(default_factory=dict)
    supported_component: SupportedComponentInfo

    model_config = ConfigDict(from_attributes=True)
