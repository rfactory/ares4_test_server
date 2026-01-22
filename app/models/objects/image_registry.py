from sqlalchemy import BigInteger, String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING # List는 사용 안되지만, 다른 모델과의 일관성을 위해 유지
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, SystemUnitFKMixin
if TYPE_CHECKING:
    from app.models.objects.device import Device
    from app.models.objects.system_unit import SystemUnit
    from app.models.objects.vision_feature import VisionFeature


class ImageRegistry(Base, TimestampMixin, DeviceFKMixin, SystemUnitFKMixin):
    """
    [Object] 수집된 원본 이미지 데이터의 자산 등록부입니다.
    데이터 자산 가치를 위해 실물은 S3/MinIO에 저장하고 경로를 기록합니다.
    """
    __tablename__ = "image_registries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 실물 데이터 경로 (S3/MinIO URL 또는 Object Key)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # 이미지 무결성 및 중복 방지용 해시 (예: SHA-256)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # 이미지 메타데이터 (가변적 정보 수용)
    # 예: {"resolution": "1920x1080", "format": "jpg", "camera_id": "cam_01"}
    image_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # --- Relationships ---
    system_unit: Mapped["SystemUnit"] = relationship("SystemUnit", back_populates="image_registries")
    device: Mapped["Device"] = relationship("Device", back_populates="image_registries")
    
    # 추출된 특징값(벡터) 목록 - SAM 3나 DeepSeek 등의 추론 결과와 연결
    vision_features: Mapped[List["VisionFeature"]] = relationship("VisionFeature", back_populates="image_registry")