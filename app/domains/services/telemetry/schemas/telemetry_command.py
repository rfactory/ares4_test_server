# --- Command-related Schemas ---
# 이 파일은 데이터의 상태를 변경하는 'Command' 작업과 관련된 Pydantic 스키마들을 정의합니다.
# (생성)

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class TelemetryCommandMetadataCreate(BaseModel):
    meta_key: str = Field(..., description="메타데이터의 키")
    meta_value: str = Field(..., description="메타데이터의 값")
    meta_value_type: str = Field("STRING", description="메타데이터 값의 타입")
    description: Optional[str] = Field(None, description="메타데이터 설명")

class TelemetryCommandDataCreate(BaseModel):
    device_id: int = Field(..., description="관련 기기의 ID")
    timestamp: datetime = Field(..., description="데이터 측정 시간")
    metric_name: str = Field(..., description="측정 항목 이름")
    metric_value: float = Field(..., description="측정된 값")
    unit: Optional[str] = Field(None, description="측정 값의 단위")
    metadata_items: Optional[List[TelemetryCommandMetadataCreate]] = Field(None, description="메타데이터 항목 목록")
