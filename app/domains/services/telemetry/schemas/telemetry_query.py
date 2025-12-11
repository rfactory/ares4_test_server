# --- Query-related Schemas ---
# 이 파일은 데이터의 상태를 변경하지 않는 'Query' 작업과 관련된 Pydantic 스키마들을 정의합니다.
# (조회)

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class TelemetryQueryMetadataRead(BaseModel):
    meta_key: str = Field(..., description="메타데이터의 키")
    meta_value: str = Field(..., description="메타데이터의 값")
    meta_value_type: str = Field("STRING", description="메타데이터 값의 타입")
    description: Optional[str] = Field(None, description="메타데이터 설명")

    class Config:
        from_attributes = True # ORM 모델로부터 읽기 위함

class TelemetryQueryDataRead(BaseModel):
    id: int = Field(..., description="텔레메트리 데이터 고유 ID")
    device_id: int = Field(..., description="관련 기기의 ID")
    timestamp: datetime = Field(..., description="데이터가 측정된 시간")
    metric_name: str = Field(..., description="측정 항목의 이름")
    metric_value: float = Field(..., description="측정된 값")
    unit: Optional[str] = Field(None, description="측정 값의 단위")
    metadata_items: Optional[List[TelemetryQueryMetadataRead]] = Field(None, description="메타데이터 항목 목록")

    class Config:
        from_attributes = True # ORM 모델로부터 읽기 위함
        json_encoders = {
            datetime: lambda dt: dt.isoformat(timespec='milliseconds')
        }

class TelemetryFilter(BaseModel):
    device_ids: Optional[List[int]] = Field(None, description="필터링할 기기 ID 리스트")
    metric_names: Optional[List[str]] = Field(None, description="필터링할 측정 항목 이름 리스트")
    start_time: Optional[datetime] = Field(None, description="조회 시작 시간")
    end_time: Optional[datetime] = Field(None, description="조회 종료 시간")
    skip: int = Field(0, ge=0, description="건너뛸 레코드 수")
    limit: int = Field(100, ge=1, le=1000, description="반환할 최대 레코드 수")
