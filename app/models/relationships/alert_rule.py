from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Boolean, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, UserFKMixin

class AlertRule(Base, TimestampMixin, DeviceFKMixin, UserFKMixin):
    """
    알림 규칙 모델은 특정 장치에서 발생하는 이벤트에 대해
    사용자에게 알림을 보낼 조건을 정의합니다.
    """
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True) # 알림 규칙의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다.
    # user_id는 UserFKMixin으로부터 상속받습니다.
    name = Column(String(100), nullable=False) # 알림 규칙의 이름
    description = Column(Text, nullable=True) # 알림 규칙에 대한 설명
    condition = Column(JSON, nullable=False) # 알림 발생 조건 (JSON 형식, 예: {'metric': 'temperature', 'operator': '>', 'value': 30})
    severity = Column(Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='alert_severity'), default='MEDIUM', nullable=False) # 알림의 심각도 ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
    notification_channels = Column(JSON, nullable=True) # 알림을 전송할 채널 목록 (JSON 형식, 예: ['email', 'sms', 'app_push'])
    is_active = Column(Boolean, default=True, nullable=False) # 알림 규칙의 활성화 여부
    
    # --- Relationships ---
    device = relationship("Device", back_populates="alert_rules") # 이 알림 규칙이 적용되는 장치 정보
    user = relationship("User", back_populates="alert_rules") # 이 알림 규칙을 생성하거나 관리하는 사용자 정보
    alert_events = relationship("AlertEvent", back_populates="alert_rule") # 이 알림 규칙에 의해 생성된 알림 이벤트 목록