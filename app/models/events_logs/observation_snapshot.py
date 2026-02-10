from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING, Optional

from app.database import Base
from ..base_model import TimestampMixin, SystemUnitFKMixin

if TYPE_CHECKING:
    from .telemetry_data import TelemetryData
    from ..objects.image_registry import ImageRegistry
    from ..objects.action_log import ActionLog
    from ..objects.vision_feature import VisionFeature
    from ..objects.system_unit import SystemUnit # SystemUnitFKMixin을 위한 타입

class ObservationSnapshot(Base, TimestampMixin, SystemUnitFKMixin):
    """
    [Master] 특정 시점의 모든 관측 데이터(센서 + 비전)를 하나로 묶는 마스터 테이블입니다.
    RL 모델은 이 테이블의 ID를 기준으로 전체 상태(State)를 조회합니다.
    """
    __tablename__ = "observation_snapshots"
    
    # Snapshot ID는 시계열 데이터 식별을 위해 String(UUID 또는 Timestamp 조합)으로 유지
    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True, comment="고유 스냅샷 ID")
    
    observation_type: Mapped[str] = mapped_column(
        Enum('IMAGE', 'SENSOR', 'LOG', 'ALARM', 'COMMAND', name='observation_snapshot_type', create_type=False),
        nullable=False,
        comment="데이터 정체성 (IMAGE, SENSOR 등)"
    )
    
    # --- Relationships (Mapped 적용 완료) ---
    
    # 1. 소속 시스템 유닛 (SystemUnitFKMixin 기반)
    system_unit: Mapped["SystemUnit"] = relationship("SystemUnit", back_populates="observation_snapshots")

    # 2. 센서 텔레메트리 (1:N)
    telemetry_data: Mapped[List["TelemetryData"]] = relationship("TelemetryData", back_populates="snapshot", cascade="all, delete-orphan")
    
    # 3. 이미지 정보 (1:N - 보통 1개지만 확장성 고려)
    image_registry: Mapped[List["ImageRegistry"]] = relationship("ImageRegistry", back_populates="snapshot", cascade="all, delete-orphan")
    
    # 4. 결정/추론 로그 (1:N - 이 스냅샷을 보고 RL이 판단한 결과)
    action_logs: Mapped[List["ActionLog"]] = relationship("ActionLog", back_populates="snapshot")

    # 5. 비전 특징 벡터 (1:N - 이미지에서 추출된 수치 데이터)
    vision_features: Mapped[List["VisionFeature"]] = relationship("VisionFeature", back_populates="snapshot", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ObservationSnapshot(id={self.id}, type={self.observation_type})>"