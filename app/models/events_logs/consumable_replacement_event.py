from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, UserFKMixin, UserConsumableFKMixin # Mixin 추가

class ConsumableReplacementEvent(Base, TimestampMixin, DeviceFKMixin, UserFKMixin, UserConsumableFKMixin): # Mixin 상속
    """
    소모품 교체 이벤트 모델은 장치에 사용된 소모품이 교체된 기록을 저장합니다.
    이는 소모품 사용 이력 및 유지보수 추적에 사용됩니다.
    """
    __tablename__ = "consumable_replacement_events"

    id = Column(Integer, primary_key=True, index=True, comment="소모품 교체 이벤트의 고유 ID")
    # device_id는 DeviceFKMixin으로부터 상속받습니다.
    # user_id는 UserFKMixin으로부터 상속받습니다.
    # user_consumable_id는 UserConsumableFKMixin으로부터 상속받습니다. (replaced_consumable_id로 사용)
    replacement_date = Column(DateTime(timezone=True), nullable=False)  # 소모품이 교체된 날짜 및 시간
    reason = Column(Text, nullable=True)  # 소모품 교체 사유
    
    # --- Relationships ---
    device = relationship("Device", back_populates="consumable_replacement_events") # 소모품이 교체된 장치 정보
    user = relationship("User", back_populates="consumable_replacement_events") # 소모품 교체 이벤트를 기록한 사용자 정보
    replaced_consumable = relationship("UserConsumable", back_populates="consumable_replacement_events") # 교체된 소모품 인스턴스 정보