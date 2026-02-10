from sqlalchemy import BigInteger, String, Index, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, Dict, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, SystemUnitFKMixin

if TYPE_CHECKING:
    from app.models.objects.device import Device
    from app.models.objects.system_unit import SystemUnit
    from app.models.objects.vision_feature import VisionFeature
    from ..events_logs.observation_snapshot import ObservationSnapshot

class ImageRegistry(Base, TimestampMixin, DeviceFKMixin, SystemUnitFKMixin):
    """
    [Object] 수집된 원본 이미지 데이터의 자산 등록부:
    10초 주기의 Telemetry 데이터와 snapshot_id를 통해 동기화되며, 
    비전 모델의 학습 및 추론 근거(Evidence)로 활용됩니다.
    """
    __tablename__ = "image_registries"
    __table_args__ = (
        Index('idx_image_snapshot_id', 'snapshot_id'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # Snapshot과의 연결 (ObservationSnapshot.id는 str임에 주의)
    snapshot_id: Mapped[str] = mapped_column(
        String(255), 
        ForeignKey("observation_snapshots.id"), 
        nullable=False, 
        comment="센서 및 Action 데이터와 동기화를 위한 고유 키"
    )

    # 저장 정보
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False, comment="S3/MinIO 저장 경로")
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True, comment="이미지 무결성 체크용 해시")

    # 가변 메타데이터 (JSONB)
    # 예: {"resolution": "1920x1080", "exposure": 100, "camera_id": "CAM_01"}
    image_metadata: Mapped[Optional[Dict]] = mapped_column(postgresql.JSONB, nullable=True, comment="카메라 설정 등 가변 메타데이터")

    # --- Relationships (Mapped 적용 완료) ---
    
    # 1. 시점 동기화 (Snapshot)
    snapshot: Mapped["ObservationSnapshot"] = relationship(
        "ObservationSnapshot", back_populates="image_registry"
    )
    
    # 2. 소속 인프라 (SystemUnit, Device)
    system_unit: Mapped["SystemUnit"] = relationship(
        "SystemUnit", back_populates="image_registries"
    )
    device: Mapped["Device"] = relationship(
        "Device", back_populates="image_registries"
    )
    
    # 3. 파생 데이터 (이미지 분석 결과)
    vision_features: Mapped[List["VisionFeature"]] = relationship(
        "VisionFeature", 
        back_populates="image_registry",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ImageRegistry(id={self.id}, path={self.storage_path})>"