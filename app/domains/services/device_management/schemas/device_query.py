from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

# 1. 하위 관계 모델을 먼저 정의합니다.
class OrganizationDeviceRead(BaseModel):
    """장치와 조직 간의 관계 정보"""
    organization_id: int
    relationship_type: str  # 'OWNER', 'OPERATOR', 'VIEWER'
    model_config = ConfigDict(from_attributes=True)
    
class UserDeviceRead(BaseModel):
    """장치와 개인 사용자 간의 관계 정보"""
    user_id: int
    role: str  # 'owner', 'viewer'
    model_config = ConfigDict(from_attributes=True)

# 2. 메인 모델에서 위 모델들을 참조합니다.
class DeviceRead(BaseModel):
    """클라이언트에 반환될 장치 데이터 (읽기 전용)."""
    id: int = Field(..., description="장치의 고유 ID")
    cpu_serial: str = Field(..., description="CPU 시리얼")
    current_uuid: UUID = Field(..., description="장치에 할당된 현재 UUID")
    hardware_blueprint_id: int = Field(..., description="장치의 하드웨어 블루프린트 ID")
    system_unit_id: Optional[int] = Field(None, description="장치가 소속된 시스템 유닛 ID")
    visibility_status: str = Field("PRIVATE", description="장치의 공개 범위 상태")
    status: str = Field("UNKNOWN", description="장치의 현재 상태")
    
    # 이제 정상적으로 참조 가능합니다.
    organization_devices: List[OrganizationDeviceRead] = Field(
        default_factory=list, description="연결된 조직 리스트"
    )
    users: List[UserDeviceRead] = Field(
        default_factory=list, description="연결된 사용자 리스트"
    )
    
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
    skip: int = Field(0, ge=0, description="건너뛸 레코드 수")
    limit: int = Field(100, ge=1, le=1000, description="반환할 최대 레코드 수")