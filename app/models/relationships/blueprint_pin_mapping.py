from sqlalchemy import Column, BigInteger, String, UniqueConstraint, Integer # Integer 추가
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

from app.database import Base
from ..base_model import TimestampMixin, HardwareBlueprintFKMixin, SupportedComponentFKMixin

class BlueprintPinMapping(Base, TimestampMixin, HardwareBlueprintFKMixin, SupportedComponentFKMixin):
    """
    [Relationship] 블루프린트 핀 매핑 모델입니다.
    특정 라즈베리파이 도면(HardwareBlueprint)에서 각 부품(SupportedComponent)이
    물리적으로 어느 핀에 연결되는지 정의하는 '회로도' 역할을 합니다.
    """
    __tablename__ = "blueprint_pin_mappings"
    __table_args__ = (
        # 동일한 도면 내에서 같은 부품이 같은 핀 이름을 중복해서 가질 수 없도록 보장
        UniqueConstraint('hardware_blueprint_id', 'supported_component_id', 'pin_name', name='_blueprint_component_pin_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 핀의 논리적 이름 및 물리적 설정
    pin_name: Mapped[str] = mapped_column(String(50), nullable=False) # 예: 'DHT11_DATA'
    pin_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 실제 GPIO 번호 (예: 4)
    pin_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # 'INPUT', 'OUTPUT', 'PWM' 등
    
    # --- Relationships ---
    blueprint = relationship("HardwareBlueprint", back_populates="blueprint_pin_mappings")
    supported_component = relationship("SupportedComponent", back_populates="blueprint_pin_mappings")
    pin_details = relationship("BlueprintPinDetail", back_populates="blueprint_pin_mapping")