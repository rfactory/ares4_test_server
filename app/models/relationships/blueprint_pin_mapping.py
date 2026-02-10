from sqlalchemy import BigInteger, String, UniqueConstraint, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING

from app.database import Base
from ..base_model import TimestampMixin, HardwareBlueprintFKMixin, SupportedComponentFKMixin

if TYPE_CHECKING:
    from app.models.objects.hardware_blueprint import HardwareBlueprint
    from app.models.objects.supported_component import SupportedComponent
    from app.models.relationships.blueprint_pin_detail import BlueprintPinDetail

class BlueprintPinMapping(Base, TimestampMixin, HardwareBlueprintFKMixin, SupportedComponentFKMixin):
    """
    [Relationship] 블루프린트 핀 매핑 모델:
    특정 설계도(HardwareBlueprint) 내에서 각 부품(SupportedComponent)이 
    물리적으로 어느 GPIO 핀에 연결되는지 정의하는 '회로도' 역할을 수행합니다.
    """
    __tablename__ = "blueprint_pin_mappings"
    __table_args__ = (
        # 동일 설계도 내에서 부품과 핀 이름의 조합이 중복되는 것을 방지
        UniqueConstraint('hardware_blueprint_id', 'supported_component_id', 'pin_name', name='_blueprint_component_pin_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 핀의 논리적 이름 (예: 'TEMP_SENSOR_DATA')
    pin_name: Mapped[str] = mapped_column(String(50), nullable=False) 
    
    # 실제 GPIO 번호 (예: 14)
    pin_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) 
    
    # 동작 모드 (예: 'INPUT', 'OUTPUT', 'I2C_SDA', 'PWM')
    pin_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) 
    
    # --- Relationships (Mapped 적용 완료) ---

    # 1. 상위 설계도와의 연결
    blueprint: Mapped["HardwareBlueprint"] = relationship(
        "HardwareBlueprint", back_populates="blueprint_pin_mappings"
    )
    
    # 2. 연결된 부품 규격과의 연결
    supported_component: Mapped["SupportedComponent"] = relationship(
        "SupportedComponent", back_populates="blueprint_pin_mappings"
    )
    
    # 3. 상세 사양 (전압, 프로토콜 등)과의 연결
    pin_details: Mapped[List["BlueprintPinDetail"]] = relationship(
        "BlueprintPinDetail", 
        back_populates="blueprint_pin_mapping",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<BlueprintPinMapping(pin={self.pin_name}, num={self.pin_number}, mode={self.pin_mode})>"