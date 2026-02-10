from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class SupportedComponentBase(BaseModel):
    """조회/생성/수정 시 공통으로 사용할 기반 스키마"""
    name: str = Field(validation_alias="display_name")
    version: str = Field(validation_alias="model_name")
    manufacturer: Optional[str] = None
    component_type: str = Field(validation_alias="category")
    unit: Optional[str] = None

class SupportedComponentRead(SupportedComponentBase):
    """데이터 조회 시 반환될 모델"""
    id: int

    model_config = ConfigDict(from_attributes=True)
