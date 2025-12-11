from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, UserFKMixin

class Schedule(Base, TimestampMixin, DeviceFKMixin, UserFKMixin):
    """
    스케줄 모델은 특정 장치에서 특정 시간에 수행될 작업을 정의합니다.
    반복 패턴을 설정하여 주기적인 작업을 자동화할 수 있습니다.
    """
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True) # 스케줄의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다.
    # user_id는 UserFKMixin으로부터 상속받습니다.
    name = Column(String(100), nullable=False) # 스케줄의 이름
    description = Column(Text, nullable=True) # 스케줄에 대한 설명
    start_time = Column(DateTime(timezone=True), nullable=False) # 스케줄 시작 시간
    end_time = Column(DateTime(timezone=True), nullable=True) # 스케줄 종료 시간 (Null이면 무기한)
    recurrence_pattern = Column(JSON, nullable=True) # 스케줄 반복 패턴 (JSON 형식, 예: {'type': 'daily', 'interval': 1})
    is_active = Column(Boolean, default=True, nullable=False) # 스케줄의 활성화 여부
    action_details = Column(JSON, nullable=False) # 스케줄에 따라 수행할 작업의 상세 정보 (JSON 형식, 예: {'component_id': 1, 'action': 'turn_on'})
    
    # --- Relationships ---
    device = relationship("Device", back_populates="schedules") # 이 스케줄이 적용되는 장치 정보
    user = relationship("User", back_populates="schedules") # 이 스케줄을 생성하거나 관리하는 사용자 정보