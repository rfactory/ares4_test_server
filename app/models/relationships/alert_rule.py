from sqlalchemy import BigInteger, String, Text, JSON, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from app.database import Base
from ..base_model import TimestampMixin, UserFKMixin

class AlertRule(Base, TimestampMixin, UserFKMixin):
    """
    [Object] 알림 규칙 모델입니다.
    개별 라즈베리파이가 아닌 'SystemUnit(클러스터)' 단위를 기본 감시 대상으로 하며, 
    강화학습 모델이 유닛 전체의 상태를 분석하여 알림을 발생시키는 기준이 됩니다.
    """
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # --- 핵심: 클러스터(SystemUnit) 중심 연결 ---
    # 사용자가 관리하는 '전체적인 관점'의 알림 대상입니다.
    system_unit_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('system_units.id'), nullable=False, index=True)
    
    # "특별한 일"이 있을 때만 특정 장치를 타겟팅할 수 있도록 Nullable로 유지합니다.
    device_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('devices.id'), nullable=True, index=True)
    
    # user_id는 UserFKMixin으로부터 상속받습니다. (BigInteger)

    name: Mapped[str] = mapped_column(String(100), nullable=False) # 알림 규칙 이름
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 알림 규칙 설명
    
    # 알림 발생 조건 (JSON 형식)
    # 예: {'target': 'cluster_avg', 'metric': 'temp', 'operator': '>', 'value': 35}
    condition: Mapped[dict] = mapped_column(JSON, nullable=False) 
    
    # 알림의 심각도
    severity: Mapped[str] = mapped_column(Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='alert_severity'), default='MEDIUM', nullable=False)
    
    # 알림 전송 채널 (JSON 형식)
    notification_channels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) 
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # 활성화 여부

    # --- Relationships ---
    system_unit = relationship("SystemUnit", back_populates="alert_rules")
    device = relationship("Device", back_populates="alert_rules")
    user = relationship("User", back_populates="alert_rules")
    alert_events = relationship("AlertEvent", back_populates="alert_rule")