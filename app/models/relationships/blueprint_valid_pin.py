from sqlalchemy import Column, BigInteger, String, UniqueConstraint, Integer # Integer 추가
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

from app.database import Base
from ..base_model import TimestampMixin, HardwareBlueprintFKMixin

class BlueprintValidPin(Base, TimestampMixin, HardwareBlueprintFKMixin):
    """
    블루프린트 유효 핀 모델은 특정 하드웨어 블루프린트에서
    물리적으로 사용 가능한 핀의 목록과 그 특성을 정의합니다.
    """
    __tablename__ = "blueprint_valid_pins"
    __table_args__ = (
        # 특정 하드웨어 설계도 내에서 핀 번호는 중복될 수 없습니다.
        UniqueConstraint('hardware_blueprint_id', 'pin_number', name='_blueprint_valid_pin_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 해당 라즈베리파이/보드 모델에서 실제로 존재하는 물리 핀 번호
    pin_number: Mapped[int] = mapped_column(Integer, nullable=False) 
    pin_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # 예: 'GPIO', 'I2C_SDA', '5V'
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) 
    
    # --- Relationships ---
    blueprint = relationship("HardwareBlueprint", back_populates="blueprint_valid_pins")