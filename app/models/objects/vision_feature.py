from sqlalchemy import BigInteger, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING # TYPE_CHECKING 추가
from app.database import Base
from ..base_model import TimestampMixin, SystemUnitFKMixin, DeviceFKMixin

# 런타임 순환 참조 방지 및 타입 힌트 지원
if TYPE_CHECKING:
    from app.models.objects.image_registry import ImageRegistry
    from app.models.objects.system_unit import SystemUnit
    from app.models.objects.device import Device

class VisionFeature(Base, TimestampMixin, SystemUnitFKMixin, DeviceFKMixin):
    """
    [Object] 이미지에서 추출된 AI 특징값(Vector/Embedding) 객체입니다.
    RL 모델이 시각적 상태를 판단하는 핵심 수치 데이터로 활용됩니다.
    """
    __tablename__ = "vision_features"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 특징값 고유 ID
    image_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("image_registries.id"), nullable=False, index=True) # 원본 이미지 ID (BigInteger)
    vector_data: Mapped[dict] = mapped_column(JSON, nullable=False) # 추출된 고차원 벡터 데이터
    model_version: Mapped[str] = mapped_column(String(50), nullable=False) # 사용된 모델 (SAM3, 경량 모델 등)
    
    # --- Relationships ---
    image_registry: Mapped["ImageRegistry"] = relationship("ImageRegistry", back_populates="vision_features")
    system_unit: Mapped["SystemUnit"] = relationship("SystemUnit", back_populates="vision_features")
    device: Mapped["Device"] = relationship("Device", back_populates="vision_features")
