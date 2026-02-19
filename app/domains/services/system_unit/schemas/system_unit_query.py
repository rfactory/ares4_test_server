from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from app.models.objects.system_unit import UnitStatus

class SystemUnitRead(BaseModel):
    """
    [Response Schema] 시스템 유닛의 상세 정보를 반환하기 위한 스키마
    """
    id: int = Field(..., description="시스템 유닛 고유 ID")
    name: str = Field(..., description="시스템 유닛 이름")
    master_device_id: Optional[int] = Field(None, description="현재 할당된 마스터 기기 ID")
    status: UnitStatus = Field(..., description="유닛의 현재 상태 (ACTIVE, PROVISIONING 등)")
    product_line_id: int = Field(..., description="이 유닛이 속한 제품 라인 ID")
    
    # JSONB 데이터
    unit_config: Optional[Dict[str, Any]] = Field(None, description="유닛별 가변 설정 값")
    description: Optional[str] = Field(None, description="유닛 상세 설명")

    model_config = ConfigDict(from_attributes=True)