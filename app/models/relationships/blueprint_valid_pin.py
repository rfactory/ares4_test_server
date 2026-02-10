from sqlalchemy import BigInteger, String, UniqueConstraint, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING

from app.database import Base
from ..base_model import TimestampMixin, HardwareBlueprintFKMixin

if TYPE_CHECKING:
    from app.models.objects.hardware_blueprint import HardwareBlueprint

class BlueprintValidPin(Base, TimestampMixin, HardwareBlueprintFKMixin):
    """
    [Object] 블루프린트 유효 핀 모델:
    특정 하드웨어 설계도(예: RPi 5)에서 물리적으로 사용 가능한 핀의 목록과 그 전기적 특성을 정의합니다.
    시스템이 허용되지 않은 핀에 부품을 매핑하는 것을 방지하는 가드레일 역할을 합니다.
    """
    __tablename__ = "blueprint_valid_pins"
    __table_args__ = (
        # 특정 하드웨어 설계도 내에서 핀 번호 중복 방지
        UniqueConstraint('hardware_blueprint_id', 'pin_number', name='_blueprint_valid_pin_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 해당 보드 모델에서 실제로 존재하는 물리 핀 번호 (Header Pin Number)
    pin_number: Mapped[int] = mapped_column(Integer, nullable=False) 
    
    # 핀의 물리적 성격 (예: 'GPIO', 'I2C_SDA', '5V', 'GND', 'ADC')
    pin_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) 
    
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) 
    
    # --- Relationships (Mapped 적용 완료) ---
    # 상위 설계도 객체
    blueprint: Mapped["HardwareBlueprint"] = relationship(
        "HardwareBlueprint", 
        back_populates="blueprint_valid_pins"
    )

    def __repr__(self):
        return f"<BlueprintValidPin(pin={self.pin_number}, type={self.pin_type})>"