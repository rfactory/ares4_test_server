from sqlalchemy import BigInteger, ForeignKey, String, Index
from sqlalchemy.dialects import postgresql  # JSONB 지원을 위해 추가
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, SystemUnitFKMixin, DeviceFKMixin

if TYPE_CHECKING:
    from app.models.objects.image_registry import ImageRegistry
    from app.models.objects.system_unit import SystemUnit
    from app.models.objects.device import Device
    from app.models.events_logs.observation_snapshot import ObservationSnapshot

class VisionFeature(Base, TimestampMixin, SystemUnitFKMixin, DeviceFKMixin):
    """
    [Object] 이미지 특징값 객체:
    SAM3, YOLO 등을 통해 추출된 고차원 벡터 또는 객체 인식 결과(BBox 등)를 저장합니다.
    RL 에이전트의 State 구성을 위한 핵심 시각 지표로 활용됩니다.
    """
    __tablename__ = "vision_features"
    __table_args__ = (
        Index('idx_vision_snapshot_id', 'snapshot_id'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 1. 원본 소스 연결
    image_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("image_registries.id"), 
        nullable=False, 
        index=True
    )
    
    # 2. 상태 동기화 (성능 최적화 포인트)
    snapshot_id: Mapped[str] = mapped_column(
        String(255), 
        ForeignKey("observation_snapshots.id"), 
        nullable=False, 
        comment="RL State 구성을 위한 시점 동기화 키"
    )

    # 3. 데이터 및 AI 모델 정보
    # PostgreSQL의 JSONB를 사용하여 벡터 데이터 검색 및 필터링 성능 확보
    vector_data: Mapped[dict] = mapped_column(
        postgresql.JSONB, 
        nullable=False, 
        comment="추출된 벡터 또는 객체 인식 정보 (JSONB)"
    )
    
    model_version: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        index=True,
        comment="추출에 사용된 AI 모델 명칭 및 버전 (예: SAM3-v1)"
    )
    
    # --- Relationships (Mapped 적용 완료) ---
    
    # 시점 데이터 바구니 (Snapshot)
    snapshot: Mapped["ObservationSnapshot"] = relationship(
        "ObservationSnapshot", back_populates="vision_features"
    )
    
    # 원본 이미지 레지스트리
    image_registry: Mapped["ImageRegistry"] = relationship(
        "ImageRegistry", back_populates="vision_features"
    )
    
    # 인프라 연결 (수정 포인트: "Unit" -> "SystemUnit")
    system_unit: Mapped["SystemUnit"] = relationship(
        "SystemUnit", 
        back_populates="vision_features"
    )
    
    device: Mapped["Device"] = relationship(
        "Device", back_populates="vision_features"
    )