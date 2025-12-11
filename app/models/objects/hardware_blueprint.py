# app/models/objects/hardware_blueprint.py
from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, ProductLineFKMixin # ProductLineFKMixin 추가
class HardwareBlueprint(Base, TimestampMixin, ProductLineFKMixin): # ProductLineFKMixin 상속
    """
    하드웨어 블루프린트 모델은 특정 장치 유형의 설계 및 구성을 정의합니다.
    각 블루프린트는 고유한 버전과 이름을 가지며, 특정 제품 라인에 속합니다.
    """
    __tablename__ = "hardware_blueprints"
    __table_args__ = (
        UniqueConstraint('blueprint_version', 'blueprint_name', name='_blueprint_version_name_uc'),
    )

    id = Column(Integer, primary_key=True, index=True) # 하드웨어 블루프린트의 고유 ID
    blueprint_version = Column(String(50), nullable=False) # 하드웨어 블루프린트의 버전 (예: '1.0.0')
    blueprint_name = Column(String(50), nullable=False) # 하드웨어 블루프린트의 고유 이름 (예: 'SmartFarm_Sensor_V1')
    description = Column(String(255), nullable=True) # 하드웨어 블루프린트에 대한 설명
    
    # --- 관계 정의 (외래 키) ---
    # product_line_id는 ProductLineFKMixin으로부터 상속받습니다.
    
    # --- Relationships ---
    product_line = relationship("ProductLine", back_populates="hardware_blueprints") # 이 블루프린트가 속한 제품 라인
    devices = relationship("Device", back_populates="hardware_blueprint") # 이 블루프린트를 사용하는 장치 목록
    blueprint_valid_pins = relationship("BlueprintValidPin", back_populates="blueprint") # 이 블루프린트에서 유효한 핀 구성 목록
    internal_blueprint_components = relationship("InternalBlueprintComponent", back_populates="blueprint") # 이 블루프린트를 구성하는 내부 컴포넌트 목록
    blueprint_pin_mappings = relationship("BlueprintPinMapping", back_populates="blueprint") # 이 블루프린트의 핀 매핑 목록
    plan_applicable_blueprints = relationship("PlanApplicableBlueprint", back_populates="hardware_blueprint") # 이 블루프린트가 적용 가능한 구독 플랜 목록
    production_events = relationship("ProductionEvent", back_populates="hardware_blueprint") # 이 블루프린트와 관련된 생산 관리 이벤트 목록
    firmware_updates = relationship("FirmwareUpdate", back_populates="hardware_blueprint")  # 누락된 관계 추가 (FirmwareUpdate에서 참조)