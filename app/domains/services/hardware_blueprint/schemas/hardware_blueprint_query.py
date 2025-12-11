from typing import List, Optional
from pydantic import BaseModel, Field

class HardwareBlueprintRead(BaseModel):
    id: int = Field(..., description="하드웨어 블루프린트 고유 ID")
    blueprint_version: str = Field(..., description="하드웨어 블루프린트의 버전")
    blueprint_name: str = Field(..., description="하드웨어 블루프린트의 고유 이름")
    description: Optional[str] = Field(None, description="하드웨어 블루프린트에 대한 설명")
    product_line_id: Optional[int] = Field(None, description="이 블루프린트가 속한 제품 라인 ID")

    model_config = {
        "from_attributes": True,
    }

class HardwareBlueprintQuery(BaseModel):
    id: Optional[int] = Field(None, description="필터링할 하드웨어 블루프린트 ID")
    blueprint_version: Optional[str] = Field(None, description="필터링할 블루프린트 버전")
    blueprint_name: Optional[str] = Field(None, description="필터링할 블루프린트 이름")
    product_line_id: Optional[int] = Field(None, description="필터링할 제품 라인 ID")
    skip: int = Field(0, ge=0, description="건너뛸 레코드 수")
    limit: int = Field(100, ge=1, le=1000, description="반환할 최대 레코드 수")
