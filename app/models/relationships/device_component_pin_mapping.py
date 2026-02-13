from sqlalchemy import BigInteger, String, UniqueConstraint, Integer, Enum as SA_Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
import enum

from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, DeviceComponentInstanceFKMixin

if TYPE_CHECKING:
    from ..relationships.device_component_instance import DeviceComponentInstance
    from ..objects.device import Device

class PinStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"   # 정상 (운영 및 수정 가능)
    FAULTY = "FAULTY"   # 고장 (제어 로직 제외 및 수정 불가)

class DeviceComponentPinMapping(Base, TimestampMixin, DeviceFKMixin, DeviceComponentInstanceFKMixin):
    """
    [Relationship] 장치 컴포넌트 핀 매핑:
    특정 장치 인스턴스에 설치된 부품의 논리적 핀이 본체의 물리적 GPIO 핀에 
    어떻게 연결되어 있는지를 기록하는 '최종 배선 실명제' 모델입니다.
    """
    __tablename__ = "device_component_pin_mappings"
    __table_args__ = (
        # 한 부품 인스턴스 내에서 핀 이름은 중복될 수 없음
        UniqueConstraint('device_component_instance_id', 'pin_name', name='_device_component_pin_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 핀의 논리적 역할 (예: 'DATA', 'VCC', 'GND', 'PWM_SIGNAL')
    pin_name: Mapped[str] = mapped_column(String(50), nullable=False) 
    
    # 실제 장치에 꽂힌 물리 핀 번호 (예: 17)
    pin_number: Mapped[int] = mapped_column(Integer, nullable=False) 
    
    # 소프트웨어 레벨의 핀 동작 모드 (예: 'INPUT', 'OUTPUT', 'ALT0')
    pin_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) 

    # 상태 Enum 적용
    status: Mapped[PinStatusEnum] = mapped_column(
        SA_Enum(PinStatusEnum, name="pin_status_enum", create_type=True), # 최초 생성 시 True
        default=PinStatusEnum.ACTIVE,
        nullable=False
    )

    # --- Relationships ---
    
    device_component_instance: Mapped["DeviceComponentInstance"] = relationship(
        "DeviceComponentInstance", 
        back_populates="pin_mappings"
    )
    
    device: Mapped["Device"] = relationship(
        "Device", 
        back_populates="pin_mappings"
    )

    def __repr__(self):
        return f"<DeviceComponentPinMapping(pin={self.pin_name}, physical_no={self.pin_number}, status={self.status})>"