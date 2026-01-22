from sqlalchemy import BigInteger, String, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from datetime import datetime  # 추가 필요

from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, UserFKMixin

class Schedule(Base, TimestampMixin, DeviceFKMixin, UserFKMixin):
    """
    [Instruction Layer] 스케줄 모델입니다.
    특정 장치(Device)가 정해진 시간에 어떤 동작(Action)을 수행할지 정의합니다.
    """
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 기본 정보
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 시간 설정
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 반복 및 제어 로직 (JSON 활용)
    # 예: {'type': 'weekly', 'days': [1, 3, 5], 'time': '08:00:00'}
    recurrence_pattern: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 구체적인 명령 내용
    # 예: {'component_instance_id': 501, 'command': 'set_speed', 'value': 80}
    action_details: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    device = relationship("Device", back_populates="schedules")
    user = relationship("User", back_populates="schedules")