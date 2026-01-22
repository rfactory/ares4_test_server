# app/models/objects/hardware_blueprint.py
from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional # <--- 누락된 임포트 추가
from app.database import Base
from ..base_model import TimestampMixin, ProductLineFKMixin

class HardwareBlueprint(Base, TimestampMixin, ProductLineFKMixin):
    """
    [Object] 하드웨어 블루프린트 모델입니다.
    특정 기기 유형(예: 'RPi5_Vision_Set')의 물리적 구성을 정의하며, 
    SystemUnit(클러스터)을 구성하는 개별 하드웨어의 명세서 역할을 합니다.
    """
    __tablename__ = "hardware_blueprints"
    __table_args__ = (
        UniqueConstraint('blueprint_version', 'blueprint_name', name='_blueprint_version_name_uc'),
    )

    # BigInteger PK로 타입 일관성 확보
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    blueprint_version: Mapped[str] = mapped_column(String(50), nullable=False)
    blueprint_name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- Relationships ---
    # 이 설계도가 속한 제품군 (예: SmartFarm)
    product_line = relationship("ProductLine", back_populates="hardware_blueprints")
    
    # 이 설계도를 기반으로 생성된 실제 물리 장치들
    devices = relationship("Device", back_populates="hardware_blueprint")
    
    # --- 기존 관계 유지 ---
    blueprint_valid_pins = relationship("BlueprintValidPin", back_populates="blueprint")
    internal_blueprint_components = relationship("InternalBlueprintComponent", back_populates="blueprint")
    blueprint_pin_mappings = relationship("BlueprintPinMapping", back_populates="blueprint")
    # 오타 수정: Firmback_populatesareUpdate -> FirmwareUpdate
    firmware_updates = relationship("FirmwareUpdate", back_populates="hardware_blueprint")