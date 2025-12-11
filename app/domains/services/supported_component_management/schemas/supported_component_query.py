# Pydantic 모델을 사용하여 데이터 조회 시의 데이터 형태를 정의합니다.

from pydantic import BaseModel, ConfigDict

class SupportedComponentBase(BaseModel):
    """조회/생성/수정 시 공통으로 사용할 기반 스키마"""
    name: str
    version: str
    manufacturer: str
    component_type: str

class SupportedComponentRead(SupportedComponentBase):
    """데이터 조회 시 반환될 모델"""
    id: int

    model_config = ConfigDict(from_attributes=True)
