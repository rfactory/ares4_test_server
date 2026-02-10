from typing import Optional, List
from pydantic import BaseModel, Field

# =========================================================
# 1. 하드웨어 스펙 정의 (Query 파일과 동일한 구조)
# (팁: 나중에는 이 클래스들을 common.py 같은 곳으로 빼서 공유하는 것이 좋습니다)
# =========================================================

class Dimensions(BaseModel):
    width_mm: float = Field(..., gt=0, description="PCB 가로 길이 (mm)")
    height_mm: float = Field(..., gt=0, description="PCB 세로 길이 (mm)")
    depth_mm: Optional[float] = Field(None, gt=0, description="PCB 두께/높이 (mm)")

class PowerRequirements(BaseModel):
    input_voltage: str = Field(..., description="입력 전압 (예: '5V', '12V-24V')")
    max_current_draw: Optional[str] = Field(None, description="최대 소모 전류 (예: '2.5A')")
    connector_type: Optional[str] = Field(None, description="전원 커넥터 타입 (예: 'USB-C', 'Barrel Jack')")

class BlueprintSpecs(BaseModel):
    """
    [핵심] HardwareBlueprint.specs (JSONB) 컬럼에 들어갈 데이터 검증 모델
    """
    dimensions: Dimensions = Field(..., description="물리적 크기 정보")
    power: PowerRequirements = Field(..., description="전원 요구 사항")
    operating_temperature: str = Field("-20C to 85C", description="동작 온도 범위")
    certification: List[str] = Field(default_factory=list, description="인증 내역 (KC, CE, FCC 등)")


# =========================================================
# 2. Command (Create / Update) 스키마
# =========================================================

class HardwareBlueprintCreate(BaseModel):
    blueprint_version: str = Field(..., description="하드웨어 블루프린트의 버전")
    blueprint_name: str = Field(..., description="하드웨어 블루프린트의 고유 이름")
    description: Optional[str] = Field(None, description="하드웨어 블루프린트에 대한 설명")
    
    # User 요청대로 Optional 유지
    product_line_id: Optional[int] = Field(None, description="이 블루프린트가 속한 제품 라인 ID")
    
    # [추가] 생성 시 'specs' 필드를 필수로 받습니다.
    # (BluepinstSpecs 객체로 받으면 Pydantic이 자동으로 검증 후 JSON으로 변환합니다)
    specs: BlueprintSpecs = Field(..., description="하드웨어 물리/전기적 상세 명세")

class HardwareBlueprintUpdate(BaseModel):
    blueprint_version: Optional[str] = Field(None, description="하드웨어 블루프린트의 버전")
    blueprint_name: Optional[str] = Field(None, description="하드웨어 블루프린트의 고유 이름")
    description: Optional[str] = Field(None, description="하드웨어 블루프린트에 대한 설명")
    product_line_id: Optional[int] = Field(None, description="이 블루프린트가 속한 제품 라인 ID")
    
    # [추가] 수정 시에는 Optional로 두어, 스펙을 변경하고 싶을 때만 보냅니다.
    specs: Optional[BlueprintSpecs] = Field(None, description="업데이트할 하드웨어 명세")
    
