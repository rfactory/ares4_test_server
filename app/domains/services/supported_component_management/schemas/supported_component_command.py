# Pydantic 모델을 사용하여 데이터 생성/수정 시의 데이터 형태를 정의합니다.

from typing import Optional
from pydantic import BaseModel
from .supported_component_query import SupportedComponentBase

# --- SupportedComponent Schemas ---

class SupportedComponentCreate(SupportedComponentBase):
    """새로운 지원 부품 생성 시 사용할 모델"""
    pass

class SupportedComponentUpdate(BaseModel):
    """지원 부품 정보 수정 시 사용할 모델"""
    name: Optional[str] = None
    version: Optional[str] = None
    manufacturer: Optional[str] = None
