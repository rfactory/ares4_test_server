import enum
from sqlalchemy import String, Float, Enum, Text, Boolean, BigInteger, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    from ..relationships.device_component_instance import DeviceComponentInstance
    from ..relationships.blueprint_pin_mapping import BlueprintPinMapping
    from ..relationships.supported_component_metadata import SupportedComponentMetadata

class ControlType(str, enum.Enum):
    RANGE = "RANGE"   # 예: 밝기 0~100, 모터 속도
    BINARY = "BINARY" # 예: 릴레이 ON/OFF
    STEP = "STEP"     # 예: 서보 모터 각도 단계
    NONE = "NONE"     # 단순 센서 등 제어 불가 장치

class SupportedComponent(Base, TimestampMixin):
    """
    [Object] 지원 컴포넌트 마스터:
    전자 부품의 논리적 제어 규격 및 드라이버 메타데이터를 관리합니다.
    물리적 외형이 아닌 '전기적 로직'과 '데이터 범위'가 정의의 핵심입니다.
    """
    __tablename__ = "supported_components"
    
    __table_args__ = (
        # 데이터 범위 정합성 보장
        CheckConstraint('min_value <= max_value', name='check_min_max_range'),
        # 동일 제조사의 동일 모델명 중복 등록 방지
        UniqueConstraint('model_name', 'manufacturer', name='_model_manufacturer_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 식별 정보
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True) 
    display_name: Mapped[str] = mapped_column(String(100), nullable=False) 
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # 분류 (예: 'RELAY', 'DHT_SENSOR', 'WATER_PUMP')
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 제어 규격
    control_type: Mapped[ControlType] = mapped_column(
        Enum(ControlType, name="control_type", create_type=False), 
        nullable=False, 
        default=ControlType.NONE
    )
    
    min_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_value: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # 'Celsius', '%', 'V' 등

    # 텔레메트리 연동 키 (예: 'temperature', 'humidity')
    telemetry_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True) 
    
    # 신호 반전 여부 (Active Low 릴레이 모듈 대응)
    active_low: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default='false', nullable=False
    )

    # --- Relationships (Mapped 적용 완료) ---
    
    # 1. 설계: 이 부품이 특정 블루프린트의 어느 핀에 매핑되는지 정의
    blueprint_pin_mappings: Mapped[List["BlueprintPinMapping"]] = relationship(
        "BlueprintPinMapping", 
        back_populates="supported_component",
        cascade="all, delete-orphan"
    )
    
    # 2. 실물: 특정 기기(Device)에 실제로 장착된 부품 인스턴스들
    device_component_instances: Mapped[List["DeviceComponentInstance"]] = relationship(
        "DeviceComponentInstance", 
        back_populates="supported_component",
        passive_deletes="all" 
    )
    
    # 3. 확장: 부품별 특수 설정값 (I2C 주소, 통신 속도 등)
    metadata_items: Mapped[List["SupportedComponentMetadata"]] = relationship(
        "SupportedComponentMetadata", 
        back_populates="supported_component",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<SupportedComponent(model={self.model_name}, type={self.control_type})>"