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
    
class SupportedComponentQuery(BaseModel):
    """부품 검색용 쿼리 파라미터"""
    model_name: Optional[str] = Field(None, description="모델명으로 검색 (예: SYSTEM)")
    category: Optional[str] = Field(None, description="카테고리로 검색")
    manufacturer: Optional[str] = Field(None, description="제조사로 검색")
    
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1)