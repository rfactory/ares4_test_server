# Pydantic 모델을 사용하여 데이터 생성/수정 시의 데이터 형태를 정의합니다.

from typing import Optional
from pydantic import BaseModel

# --- DeviceComponentInstance Schemas ---

class DeviceComponentInstanceCreate(BaseModel):
    """장치에 부품 인스턴스를 연결(생성)할 때 사용할 모델"""
    device_id: int
    supported_component_id: int
    instance_name: str
    description: Optional[str] = None
