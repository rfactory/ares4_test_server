from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

class TelemetryCommandMetadataCreate(BaseModel):
    meta_key: str = Field(..., description="메타데이터의 키")
    meta_value: str = Field(..., description="메타데이터의 값")
    meta_value_type: str = Field("STRING", description="메타데이터 값의 타입")
    description: Optional[str] = Field(None, description="메타데이터 설명")

class TelemetryCommandDataCreate(BaseModel):
    device_id: int = Field(..., description="관련 기기의 ID")
    system_unit_id: Optional[int] = Field(None, description="관련 시스템 유닛 ID")
    snapshot_id: str = Field(..., description="이미지/액션 동기화를 위한 스냅샷 ID")
    captured_at: datetime = Field(default_factory=datetime.now, description="센서 측정 시각")
    component_name: str = Field(..., description="데이터가 발생한 부품 인스턴스 명칭")
    metric_name: str = Field(..., description="측정 항목명 (예: temp, vibration)")
    unit: Optional[str] = Field(None, description="단위")

    # [핵심] 10초 통계 필드 (DB 모델과 1:1 매핑)
    avg_value: float = Field(..., description="평균값")
    min_value: float = Field(..., description="최소값")
    max_value: float = Field(..., description="최대값")
    std_dev: float = Field(..., description="표준편차")
    slope: float = Field(..., description="기울기 (추세)")
    sample_count: int = Field(10, description="샘플 개수")

    # 특화 데이터용 확장 필드
    extra_stats: Optional[Dict] = Field(None, description="추가 통계 데이터 (JSON)")
    metadata_items: Optional[List[TelemetryCommandMetadataCreate]] = Field(None, description="메타데이터 리스트")
class ClusterNodeMetric(BaseModel):
    """노드별 개별 측정 항목"""
    metric_name: str
    avg_value: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    std_dev: float = 0.0
    slope: float = 0.0
    sample_count: int = 1
    timestamp: datetime
    extra: Optional[Dict] = None

class ClusterNodeData(BaseModel):
    """기기(Node)별 데이터 묶음"""
    device_uuid: str  # 슬레이브 기기의 UUID
    instance_name: str # 부품 명칭 (예: main_board, motor_alpha)
    component_type: str
    sequence_number: Optional[int] = None
    metrics: List[ClusterNodeMetric]

class ClusterTelemetryIngestionRequest(BaseModel):
    """[최상위] 마스터가 보내는 클러스터 통합 페이로드"""
    master_uuid: str   # 마스터 기기의 UUID
    snapshot_id: str
    nodes: List[ClusterNodeData]