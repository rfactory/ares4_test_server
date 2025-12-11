from typing import Optional
from pydantic import BaseModel, Field

class HardwareBlueprintCreate(BaseModel):
    blueprint_version: str = Field(..., description="하드웨어 블루프린트의 버전")
    blueprint_name: str = Field(..., description="하드웨어 블루프린트의 고유 이름")
    description: Optional[str] = Field(None, description="하드웨어 블루프린트에 대한 설명")
    product_line_id: Optional[int] = Field(None, description="이 블루프린트가 속한 제품 라인 ID")

class HardwareBlueprintUpdate(BaseModel):
    blueprint_version: Optional[str] = Field(None, description="하드웨어 블루프린트의 버전")
    blueprint_name: Optional[str] = Field(None, description="하드웨어 블루프린트의 고유 이름")
    description: Optional[str] = Field(None, description="하드웨어 블루프린트에 대한 설명")
    product_line_id: Optional[int] = Field(None, description="이 블루프린트가 속한 제품 라인 ID")
