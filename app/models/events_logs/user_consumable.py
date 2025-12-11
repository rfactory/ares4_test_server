from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, UserFKMixin, AssetDefinitionFKMixin # Mixin 추가

class UserConsumable(Base, TimestampMixin, UserFKMixin, AssetDefinitionFKMixin): # Mixin 상속
    """
    사용자 소모품 모델은 특정 사용자가 소유한 소모품의 인스턴스를 기록합니다.
    이는 사용자의 소모품 재고 및 사용 이력을 관리합니다.
    """
    __tablename__ = "user_consumables"

    id = Column(Integer, primary_key=True, index=True) # 사용자 소모품의 고유 ID
    # user_id는 UserFKMixin으로부터 상속받습니다.
    # asset_definition_id는 AssetDefinitionFKMixin으로부터 상속받습니다.
    purchase_date = Column(DateTime(timezone=True), nullable=False) # 소모품 구매 일자
    expiration_date = Column(DateTime(timezone=True), nullable=True) # 소모품의 유통기한 (소모성 자재용)
    quantity = Column(Integer, nullable=False) # 구매 시점의 소모품 수량
    current_quantity = Column(Integer, nullable=False) # 현재 남은 소모품 수량 (소모성 자재용)
    status = Column(String(50), default='ACTIVE', nullable=False) # 소모품의 현재 상태 ('ACTIVE', 'USED_UP', 'EXPIRED', 'DISCARDED')
    notes = Column(Text, nullable=True) # 소모품에 대한 추가 메모
    
    # --- Relationships ---
    user = relationship("User", back_populates="consumables") # 이 소모품을 소유한 사용자 정보
    asset_definition = relationship("InternalAssetDefinition", back_populates="user_consumables") # 이 소모품의 정의 정보
    consumable_replacement_events = relationship("ConsumableReplacementEvent", back_populates="replaced_consumable") # 이 소모품이 교체된 이벤트 기록 목록
    consumable_usage_logs = relationship("ConsumableUsageLog", back_populates="user_consumable") # 이 소모품의 사용 기록 목록