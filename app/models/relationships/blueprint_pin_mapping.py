from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, HardwareBlueprintFKMixin, SupportedComponentFKMixin # Changed BlueprintFKMixin to HardwareBlueprintFKMixin

class BlueprintPinMapping(Base, TimestampMixin, HardwareBlueprintFKMixin, SupportedComponentFKMixin): # Changed BlueprintFKMixin to HardwareBlueprintFKMixin
    """
    블루프린트 핀 매핑 모델은 특정 하드웨어 블루프린트 내에서
    지원되는 컴포넌트가 어떤 핀에 연결되는지 정의합니다.
    """
    __tablename__ = "blueprint_pin_mappings"
    __table_args__ = (
        UniqueConstraint('hardware_blueprint_id', 'supported_component_id', 'pin_name', name='_blueprint_component_pin_uc'), # Changed blueprint_id to hardware_blueprint_id
    )

    id = Column(Integer, primary_key=True, index=True) # 블루프린트 핀 매핑의 고유 ID
    # hardware_blueprint_id는 HardwareBlueprintFKMixin으로부터 상속받습니다.
    # supported_component_id는 SupportedComponentFKMixin으로부터 상속받습니다.
    pin_name = Column(String(50), nullable=False) # 핀의 논리적 이름 (예: '온도 센서 데이터 핀')
    pin_number = Column(Integer, nullable=True) # 실제 물리적 핀 번호 (옵션)
    pin_mode = Column(String(50), nullable=True) # 핀 모드 (예: 'INPUT', 'OUTPUT', 'ANALOG')
    
    # --- Relationships ---
    blueprint = relationship("HardwareBlueprint", back_populates="blueprint_pin_mappings") # 이 매핑이 속한 하드웨어 블루프린트 정보
    supported_component = relationship("SupportedComponent", back_populates="blueprint_pin_mappings") # 이 매핑에 연결된 지원되는 컴포넌트 정보
    pin_details = relationship("BlueprintPinDetail", back_populates="blueprint_pin_mapping") # 이 핀 매핑에 대한 상세 정보 목록