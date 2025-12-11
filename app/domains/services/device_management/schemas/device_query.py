# schemas/device_query.py
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class DeviceRead(BaseModel):
    """클라이언트에 반환될 장치 데이터 (읽기 전용)."""
    id: int = Field(..., description="장치의 고유 ID")
    current_uuid: UUID = Field(..., description="장치에 할당된 현재 UUID")
    hardware_blueprint_id: int = Field(..., description="장치의 하드웨어 블루프린트 ID")
    visibility_status: str = Field("PRIVATE", description="장치의 공개 범위 상태")
    status: str = Field("UNKNOWN", description="장치의 현재 상태")
    is_active: bool = Field(True, description="장치의 활성화 여부")
    last_seen_at: Optional[datetime] = Field(None, description="장치가 마지막으로 시스템에 연결된 시간")
    created_at: datetime = Field(..., description="장치 생성 시간")
    updated_at: datetime = Field(..., description="장치 마지막 업데이트 시간")

    model_config = ConfigDict(from_attributes=True)

class DeviceQuery(BaseModel):
    """장치 목록 조회 시 사용될 필터링 및 페이지네이션 파라미터."""
    id: Optional[int] = Field(None, description="필터링할 장치 ID")
    cpu_serial: Optional[str] = Field(None, description="필터링할 CPU 시리얼")
    current_uuid: Optional[UUID] = Field(None, description="필터링할 UUID")
    hardware_blueprint_id: Optional[int] = Field(None, description="필터링할 하드웨어 블루프린트 ID")
    visibility_status: Optional[str] = Field(None, description="필터링할 공개 범위 상태")
    status: Optional[str] = Field(None, description="필터링할 장치 상태")
    is_active: Optional[bool] = Field(True, description="필터링할 활성화 상태 (기본값: True)")
    skip: int = Field(0, ge=0, description="건너뛸 레코드 수")
    limit: int = Field(100, ge=1, le=1000, description="반환할 최대 레코드 수")
