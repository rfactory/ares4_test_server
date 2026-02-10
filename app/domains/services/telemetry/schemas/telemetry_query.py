from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_serializer

# --- Query-related Schemas ---

class TelemetryQueryMetadataRead(BaseModel):
    """
    메타데이터 조회용 스키마.
    텔레메트리 데이터에 부수적으로 연결된 상세 메타 정보를 읽어올 때 사용합니다.
    """
    meta_key: str = Field(..., description="메타데이터의 키")
    meta_value: str = Field(..., description="메타데이터의 값")
    meta_value_type: str = Field("STRING", description="메타데이터 값의 타입")
    description: Optional[str] = Field(None, description="메타데이터 설명")

    model_config = ConfigDict(from_attributes=True)


class TelemetryQueryDataRead(BaseModel):
    """
    텔레메트리 데이터 조회용 통합 스키마.
    DB 모델(TelemetryData)의 통계 필드들을 모두 포함하여 AI 모델 및 대시보드에 제공합니다.
    [Ares4 핵심] 10초 통계 데이터(avg, slope 등)를 포함하여 AI가 즉시 추세를 분석할 수 있게 합니다.
    """
    id: int = Field(..., description="텔레메트리 데이터 고유 ID")
    snapshot_id: str = Field(..., description="이미지 및 Action 데이터와 동기화를 위한 고유 키")
    device_id: int = Field(..., description="관련 기기의 ID")
    system_unit_id: Optional[int] = Field(None, description="관련 시스템 유닛 ID")
    
    # 데이터 식별 정보
    metric_name: str = Field(..., description="측정 항목명 (예: temp, vibration)")
    unit: Optional[str] = Field(None, description="측정 단위")

    # 10초간의 핵심 통계값 (MLP/Transformer 입력의 핵심 데이터)
    avg_value: float = Field(..., description="10초간의 샘플 평균값")
    min_value: float = Field(..., description="10초간의 샘플 최소값")
    max_value: float = Field(..., description="10초간의 샘플 최대값")
    std_dev: float = Field(..., description="10초간의 샘플 표준편차 (안정성 지표)")
    slope: float = Field(..., description="10초간의 샘플 기울기 (현재 변화 추세)")
    sample_count: int = Field(..., description="통계 계산에 사용된 실제 샘플 수")

    # 비정형 추가 데이터 및 관계 데이터
    extra_stats: Optional[Dict] = Field(
        None, 
        description="특정 서비스나 센서에만 특화된 추가 통계 데이터 (JSON)"
    )
    metadata_items: List[TelemetryQueryMetadataRead] = Field(
        default_factory=list, 
        description="연결된 메타데이터 항목 목록"
    )

    # 시간 정보
    created_at: datetime = Field(..., description="데이터가 서버에 생성된 시간")

    # [수정] Pydantic V2 방식의 직렬화 (json_encoders 대체)
    # 클라이언트(React, AI 모듈 등)가 ISO 포맷으로 일관되게 날짜를 받을 수 있도록 처리합니다.
    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime, _info):
        return dt.isoformat(timespec='milliseconds')

    model_config = ConfigDict(from_attributes=True)


class TelemetryFilter(BaseModel):
    """
    데이터 조회 필터 스키마.
    CRUD 및 Service 레이어의 필터 로직과 일치하도록 구성되었습니다.
    """
    device_ids: Optional[List[int]] = Field(None, description="필터링할 기기 ID 리스트")
    system_unit_ids: Optional[List[int]] = Field(None, description="필터링할 시스템 유닛 ID 리스트")
    snapshot_id: Optional[str] = Field(None, description="특정 스냅샷 ID(온톨로지 키) 필터")
    metric_names: Optional[List[str]] = Field(None, description="필터링할 측정 항목 이름 리스트")
    start_time: Optional[datetime] = Field(None, description="조회 시작 시간 (captured_at 기준)")
    end_time: Optional[datetime] = Field(None, description="조회 종료 시간 (captured_at 기준)")
    
    # 페이지네이션
    skip: int = Field(0, ge=0, description="건너뛸 레코드 수")
    limit: int = Field(100, ge=1, le=1000, description="반환할 최대 레코드 수 (최대 1000)")