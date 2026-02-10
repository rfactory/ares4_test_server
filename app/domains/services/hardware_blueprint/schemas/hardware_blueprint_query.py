from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# =========================================================
# 1. 공통 스펙 정의 (Command와 동일한 구조)
# (실제 프로젝트에서는 common.py 등으로 분리해서 import하는 것을 추천합니다)
# =========================================================

class Dimensions(BaseModel):
    width_mm: float = Field(..., description="PCB 가로 길이 (mm)")
    height_mm: float = Field(..., description="PCB 세로 길이 (mm)")
    depth_mm: Optional[float] = Field(None, description="PCB 두께/높이 (mm)")

class PowerRequirements(BaseModel):
    input_voltage: str = Field(..., description="입력 전압")
    max_current_draw: Optional[str] = Field(None, description="최대 소모 전류")
    connector_type: Optional[str] = Field(None, description="전원 커넥터 타입")

class BlueprintSpecs(BaseModel):
    """
    Read 모델에서 JSONB 데이터를 구조화된 객체로 반환하기 위한 모델
    """
    dimensions: Dimensions = Field(..., description="물리적 크기 정보")
    power: PowerRequirements = Field(..., description="전원 요구 사항")
    operating_temperature: str = Field(..., description="동작 온도 범위")
    certification: List[str] = Field(default_factory=list, description="인증 내역")


# =========================================================
# 2. Read (Response) 스키마
# =========================================================

class HardwareBlueprintRead(BaseModel):
    id: int = Field(..., description="하드웨어 블루프린트 고유 ID")
    blueprint_version: str = Field(..., description="하드웨어 블루프린트의 버전")
    blueprint_name: str = Field(..., description="하드웨어 블루프린트의 고유 이름")
    description: Optional[str] = Field(None, description="하드웨어 블루프린트에 대한 설명")
    product_line_id: Optional[int] = Field(None, description="이 블루프린트가 속한 제품 라인 ID")
    
    # [추가] DB의 JSONB 데이터를 Pydantic 모델로 자동 변환하여 내려줍니다.
    # 데이터가 없을 수도 있으니 Optional로 처리합니다.
    specs: Optional[BlueprintSpecs] = Field(None, description="하드웨어 물리/전기적 상세 명세")

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# 3. Query (Search Parameter) 스키마
# =========================================================

class HardwareBlueprintQuery(BaseModel):
    id: Optional[int] = Field(None, description="필터링할 하드웨어 블루프린트 ID")
    blueprint_version: Optional[str] = Field(None, description="필터링할 블루프린트 버전")
    blueprint_name: Optional[str] = Field(None, description="필터링할 블루프린트 이름")
    product_line_id: Optional[int] = Field(None, description="필터링할 제품 라인 ID")
    
    # (참고) specs 내부 데이터로 검색하려면 별도의 복잡한 로직이 필요하므로, 
    # 기본 Query 모델에는 포함하지 않는 것이 일반적입니다.
    
    skip: int = Field(0, ge=0, description="건너뛸 레코드 수")
    limit: int = Field(100, ge=1, le=1000, description="반환할 최대 레코드 수")