from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, AssetDefinitionFKMixin # NullableUserFKMixin 제거

class InternalComponentReplacementEvent(Base, TimestampMixin, DeviceFKMixin, AssetDefinitionFKMixin): # Mixin 상속 제거
    """
    내부 컴포넌트 교체 이벤트 모델은 장치 내의 하드웨어 컴포넌트 교체 기록을 저장합니다.
    이는 장치 유지보수 이력 및 자산 추적에 사용됩니다.
    """
    __tablename__ = "internal_component_replacement_events"

    id = Column(Integer, primary_key=True, index=True) # 컴포넌트 교체 이벤트의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다.
    # asset_definition_id는 AssetDefinitionFKMixin으로부터 상속받습니다. (replaced_asset_definition_id로 사용)
    replacement_date = Column(DateTime(timezone=True), nullable=False) # 컴포넌트가 교체된 날짜 및 시간
    reason = Column(Text, nullable=True) # 컴포넌트 교체 사유
    
    # 명시적으로 외래 키 컬럼 정의
    recorded_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # 컴포넌트 교체 이벤트를 기록한 사용자 ID
    
    # --- Relationships ---
    device = relationship("Device", back_populates="replacement_events") # 컴포넌트가 교체된 장치 정보
    replaced_asset_definition = relationship("InternalAssetDefinition", back_populates="replacement_events") # 교체된 컴포넌트의 자산 정의 정보
    recorded_by_user = relationship("User", foreign_keys=[recorded_by_user_id]) # 컴포넌트 교체 이벤트를 기록한 사용자 정보