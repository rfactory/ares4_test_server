from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, HardwareBlueprintFKMixin # Changed BlueprintFKMixin to HardwareBlueprintFKMixin

class BlueprintValidPin(Base, TimestampMixin, HardwareBlueprintFKMixin): # Changed BlueprintFKMixin to HardwareBlueprintFKMixin
    """
    블루프린트 유효 핀 모델은 특정 하드웨어 블루프린트에서
    물리적으로 사용 가능한 핀의 목록과 그 특성을 정의합니다.
    """
    __tablename__ = "blueprint_valid_pins"
    __table_args__ = (
        UniqueConstraint('hardware_blueprint_id', 'pin_number', name='_blueprint_valid_pin_uc'), # Changed blueprint_id to hardware_blueprint_id
    )

    id = Column(Integer, primary_key=True, index=True) # 유효 핀의 고유 ID
    # hardware_blueprint_id는 HardwareBlueprintFKMixin으로부터 상속받습니다.
    pin_number = Column(Integer, nullable=False) # 해당 블루프린트에서 사용 가능한 물리적 핀 번호
    pin_type = Column(String(50), nullable=True) # 핀의 타입 (예: 'GPIO', 'ADC', 'PWM')
    description = Column(String(255), nullable=True) # 핀에 대한 설명
    
    # --- Relationships ---
    blueprint = relationship("HardwareBlueprint", back_populates="blueprint_valid_pins") # 이 유효 핀이 속한 하드웨어 블루프린트 정보