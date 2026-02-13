import enum
from sqlalchemy import BigInteger, String, Text, JSON, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, UserFKMixin

if TYPE_CHECKING:
    from app.models.objects.system_unit import SystemUnit
    from app.models.objects.device import Device
    from app.models.objects.user import User
    from app.models.events_logs.alert_event import AlertEvent
    from app.models.objects.organization import Organization

# 1. 알림 심각도 관리를 위한 Enum
class AlertSeverity(str, enum.Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'

class AlertRule(Base, TimestampMixin, UserFKMixin):
    """
    [Object] 알림 규칙 모델:
    SystemUnit 전체의 상태를 감시하며, 설정된 임계치나 RL 모델의 판단에 따라 알림을 발생시킵니다.
    """
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # --- 감시 대상 ---
    # 클러스터(SystemUnit) 단위 감시
    system_unit_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('system_units.id'), nullable=False, index=True
    )
    
    # 특정 장치 타겟팅 (선택 사항)
    device_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey('devices.id'), nullable=True, index=True
    )
    
    # 규칙 정보
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 2. 로직 및 채널 (JSON/JSONB 활용)
    # 조건 예: {"logic": "and", "rules": [{"metric": "cpu_load", "op": ">", "val": 90}]}
    condition: Mapped[dict] = mapped_column(JSON, nullable=False) 
    
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name='alert_severity', create_type=False), 
        default=AlertSeverity.MEDIUM, 
        nullable=False
    )
    
    # 알림 전송 설정 (Slack, Email, Push 등)
    notification_channels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) 
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships (Mapped 적용 완료) ---
    system_unit: Mapped["SystemUnit"] = relationship("SystemUnit", back_populates="alert_rules")
    device: Mapped[Optional["Device"]] = relationship("Device", back_populates="alert_rules")
    user: Mapped["User"] = relationship("User", back_populates="alert_rules")
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="alert_rules"
    )
    # 이 규칙에 의해 발생한 실제 알림 사건들
    alert_events: Mapped[List["AlertEvent"]] = relationship(
        "AlertEvent", back_populates="alert_rule", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AlertRule(name={self.name}, severity={self.severity}, active={self.is_active})>"