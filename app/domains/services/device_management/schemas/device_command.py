# schemas/device_command.py
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class DeviceBase(BaseModel):
    """생성과 수정 시 공통으로 사용될 수 있는 기본 필드."""
    cpu_serial: str = Field(..., description="장치의 CPU 고유 시리얼 번호")
    hardware_blueprint_id: Optional[int] = Field(None, description="장치의 하드웨어 블루프린트 ID")

class DeviceCreate(DeviceBase):
    """새로운 장치 생성을 위한 스키마. UUID는 서버에서 생성됩니다."""
    uuid: str = Field(..., description="장치에 할당된 고유 UUID")
    system_unit_id: Optional[int] = Field(None, description="장치가 소속된 시스템 유닛 ID")
    hmac_key_name: Optional[str] = Field(None, description="Vault에 저장된 HMAC 키 경로")
    status: Optional[str] = Field("PENDING", description="장치의 초기 상태")

class DeviceUpdate(BaseModel):
    """장치 정보 수정을 위한 스키마 (모든 필드는 선택적)."""
    current_uuid: Optional[UUID] = Field(None, description="장치의 UUID")
    cpu_serial: Optional[str] = Field(None, description="장치의 CPU 시리얼")
    hardware_blueprint_id: Optional[int] = Field(None, description="장치의 하드웨어 블루프린트 ID")
    system_unit_id: Optional[int] = Field(None, description="시스템 유닛 ID")
    visibility_status: Optional[str] = Field(None, description="장치의 공개 범위 상태")
