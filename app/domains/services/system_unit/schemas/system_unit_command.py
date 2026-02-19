from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.models.objects.system_unit import UnitStatus

class SystemUnitUpdate(BaseModel):
    """
    [Input Schema] 시스템 유닛의 정보를 수정할 때 사용하는 데이터 규격
    """
    name: Optional[str] = Field(None, description="변경할 유닛 이름")
    status: Optional[UnitStatus] = Field(None, description="변경할 유닛 상태")
    unit_config: Optional[Dict[str, Any]] = Field(None, description="변경할 유닛 설정")
    description: Optional[str] = Field(None, description="상세 설명 수정")

    model_config = {"from_attributes": True}

# --- [추가] 결합 요청용 스키마 ---
class DeviceBindingRequest(BaseModel):
    """
    [Request Schema] API를 통해 기기를 유닛에 결합해달라고 요청할 때 쓰는 바디 데이터
    """
    unit_id: int = Field(..., description="결합할 대상 시스템 유닛 ID")
    device_id: int = Field(..., description="결합할 대상 기기 ID")
    role: str = Field(..., description="기기의 역할 (예: LEADER, FOLLOWER)")