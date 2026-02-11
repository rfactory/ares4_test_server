from sqlalchemy import BigInteger, String, Float, Index, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, Dict, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.dialects import postgresql

from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, SystemUnitFKMixin

if TYPE_CHECKING:
    from .telemetry_metadata import TelemetryMetadata
    from .observation_snapshot import ObservationSnapshot
    from ..objects.device import Device
    from ..objects.system_unit import SystemUnit

class TelemetryData(Base, TimestampMixin, DeviceFKMixin, SystemUnitFKMixin):
    """
    [Log] 텔레메트리 데이터 모델:
    장치에서 수집된 센서 데이터의 통계치를 저장하며, MLP 모델의 State 입력으로 사용됩니다.
    """
    __tablename__ = "telemetry_data"
    __table_args__ = (
        Index('idx_telemetry_device_time', 'device_id', 'created_at'),
        Index('idx_telemetry_system_unit_time', 'system_unit_id', 'created_at'),
        Index('idx_telemetry_snapshot_id', 'snapshot_id'),
        UniqueConstraint(
            'device_id', 'component_name', 'metric_name', 'captured_at', 
            name='_device_component_metric_time_uc'
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    snapshot_id: Mapped[str] = mapped_column(
        String(255), 
        ForeignKey("observation_snapshots.id"), 
        nullable=False, 
        comment="이미지 및 Action 데이터와 동기화를 위한 고유 키"
    )

    # --- 데이터 종류 식별 ---
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="측정 항목명 (temp, co2 등)")
    component_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="데이터가 발생한 부품 인스턴스 명칭")
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="측정 단위")

    # --- 10초간의 통계값 (AI State 입력 핵심) ---
    avg_value: Mapped[float] = mapped_column(Float, nullable=False)
    min_value: Mapped[float] = mapped_column(Float, nullable=False)
    max_value: Mapped[float] = mapped_column(Float, nullable=False)
    std_dev: Mapped[float] = mapped_column(Float, nullable=False, comment="안정성 지표")
    slope: Mapped[float] = mapped_column(Float, nullable=False, comment="추세(기울기) 지표")
    sample_count: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    
    captured_at: Mapped[datetime] = mapped_column(
        postgresql.TIMESTAMP(timezone=True), 
        nullable=False, 
        index=True,
        comment="센서에서 실제 측정된 시각"
    )

    # --- 비정형 추가 데이터 (JSONB) ---
    extra_stats: Mapped[Optional[Dict]] = mapped_column(postgresql.JSONB, nullable=True)

    # --- Relationships (Mapped 적용 완료) ---
    
    # 부모: 스냅샷 (RL 상태의 중심)
    snapshot: Mapped["ObservationSnapshot"] = relationship(
        "ObservationSnapshot", back_populates="telemetry_data"
    )
    
    # 부모: 장치 및 시스템 유닛
    device: Mapped["Device"] = relationship("Device", back_populates="telemetry_data")
    system_unit: Mapped["SystemUnit"] = relationship("SystemUnit", back_populates="telemetry_data")
    
    # 자식: 메타데이터 상세
    metadata_items: Mapped[List["TelemetryMetadata"]] = relationship(
        "TelemetryMetadata", back_populates="telemetry_data", cascade="all, delete-orphan"
    )