from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, DeviceComponentInstanceFKMixin # Mixin 추가

class DeviceComponentPinMapping(Base, TimestampMixin, DeviceFKMixin, DeviceComponentInstanceFKMixin): # Mixin 상속
    """
    장치 컴포넌트 핀 매핑 모델은 특정 장치 컴포넌트 인스턴스의 논리적 핀이
    장치의 물리적 핀에 어떻게 연결되는지 정의합니다.
    """
    __tablename__ = "device_component_pin_mappings"
    __table_args__ = (
        UniqueConstraint('device_component_instance_id', 'pin_name', name='_device_component_pin_uc'),
    )

    id = Column(Integer, primary_key=True, index=True) # 장치 컴포넌트 핀 매핑의 고유 ID
    # device_component_instance_id는 DeviceComponentInstanceFKMixin으로부터 상속받습니다.
    # device_id는 DeviceFKMixin으로부터 상속받습니다.
    pin_name = Column(String(50), nullable=False) # 핀의 논리적 이름 (예: '데이터 핀', '전원 핀')
    pin_number = Column(Integer, nullable=False) # 실제 물리적 핀 번호
    pin_mode = Column(String(50), nullable=True) # 핀 모드 (예: 'INPUT', 'OUTPUT', 'ANALOG')
    
    # --- Relationships ---
    device_component_instance = relationship("DeviceComponentInstance", back_populates="pin_mappings") # 이 핀 매핑이 속한 장치 컴포넌트 인스턴스 정보