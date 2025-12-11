# app/models/events_logs/alert_event.py
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional # Added Optional
from datetime import datetime # Added datetime

from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, AlertRuleFKMixin # UserFKMixin 제거
class AlertEvent(Base, TimestampMixin, DeviceFKMixin, AlertRuleFKMixin): # UserFKMixin 제거
    """
    알림 이벤트 모델은 특정 알림 규칙에 의해 생성된 실제 알림 이벤트를 기록합니다.
    이는 시스템의 이상 징후 및 사용자 조치 기록을 추적합니다.
    """
    __tablename__ = "alert_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) # 알림 이벤트의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다.
    # alert_rule_id는 AlertRuleFKMixin으로부터 상속받습니다.
   
    # 명시적으로 외래 키 컬럼 정의
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), nullable=True) # 이벤트를 발생시킨 사용자 ID
   
    severity: Mapped[str] = mapped_column(Enum('INFO', 'WARNING', 'CRITICAL', name='alert_severity', create_type=False), nullable=False) # 알림의 심각도 ('INFO', 'WARNING', 'CRITICAL')
    message: Mapped[str] = mapped_column(Text, nullable=False) # 알림 메시지 내용
   
    # 명시적으로 외래 키 컬럼 정의
    acknowledged_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('users.id'), nullable=True) # 알림을 확인한 사용자 ID
   
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) # 알림이 확인된 시간
   
    # --- Relationships ---
    device = relationship("Device", back_populates="alert_events") # 이 알림 이벤트를 발생시킨 장치 정보
    user = relationship("User", foreign_keys=[user_id], back_populates="alert_events_generated") # 이 알림 이벤트를 발생시킨 사용자 정보
    alert_rule = relationship("AlertRule", back_populates="alert_events") # 이 알림 이벤트를 생성한 알림 규칙 정보
    acknowledged_by_user = relationship("User", foreign_keys=[acknowledged_by_user_id], back_populates="alert_events_acknowledged") # 이 알림 이벤트를 확인한 사용자 정보