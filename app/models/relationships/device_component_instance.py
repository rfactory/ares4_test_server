from sqlalchemy import Column, BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional # Added Optional

from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, SupportedComponentFKMixin

class DeviceComponentInstance(Base, TimestampMixin, DeviceFKMixin, SupportedComponentFKMixin):
    """
    장치 컴포넌트 인스턴스 모델은 특정 장치에 설치된
    지원되는 컴포넌트의 실제 인스턴스를 나타냅니다.
    """
    __tablename__ = "device_component_instances"
    __table_args__ = (
        UniqueConstraint('device_id', 'supported_component_id', 'instance_name', name='_device_component_instance_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 장치 컴포넌트 인스턴스의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다. (BigInteger)
    # supported_component_id는 SupportedComponentFKMixin으로부터 상속받습니다. (BigInteger)
    instance_name: Mapped[str] = mapped_column(String(100), nullable=False) # 장치 내에서 이 컴포넌트 인스턴스의 고유 이름 (예: '메인 온도 센서', '펌프 1')
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 컴포넌트 인스턴스에 대한 설명
    
    # --- Relationships ---
    device = relationship("Device", back_populates="component_instances") # 이 컴포넌트 인스턴스가 설치된 장치 정보
    supported_component = relationship("SupportedComponent", back_populates="device_component_instances") # 이 컴포넌트 인스턴스의 정의 정보
    pin_mappings = relationship("DeviceComponentPinMapping", back_populates="device_component_instance") # 이 컴포넌트 인스턴스의 핀 매핑 목록