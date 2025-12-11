from sqlalchemy import Column, Integer, String, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, UserFKMixin

class TriggerRule(Base, TimestampMixin, DeviceFKMixin, UserFKMixin):
    """
    트리거 규칙 모델은 특정 장치에서 발생하는 조건에 따라
    자동으로 특정 작업을 수행하도록 정의합니다.
    """
    __tablename__ = "trigger_rules"

    id = Column(Integer, primary_key=True, index=True) # 트리거 규칙의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다.
    # user_id는 UserFKMixin으로부터 상속받습니다.
    name = Column(String(100), nullable=False) # 트리거 규칙의 이름
    description = Column(Text, nullable=True) # 트리거 규칙에 대한 설명
    condition = Column(JSON, nullable=False) # 트리거 발생 조건 (JSON 형식, 예: {'metric': 'humidity', 'operator': '<', 'value': 40})
    action = Column(JSON, nullable=False) # 트리거 발생 시 수행할 작업 (JSON 형식, 예: {'component_id': 2, 'action': 'turn_on'})
    is_active = Column(Boolean, default=True, nullable=False) # 트리거 규칙의 활성화 여부
    
    # --- Relationships ---
    device = relationship("Device", back_populates="trigger_rules") # 이 트리거 규칙이 적용되는 장치 정보
    user = relationship("User", back_populates="trigger_rules") # 이 트리거 규칙을 생성하거나 관리하는 사용자 정보
