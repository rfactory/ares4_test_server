from sqlalchemy import Column, BigInteger, DateTime, Float, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.sql import func

from app.database import Base
from ..base_model import TimestampMixin, LogBaseMixin, UserFKMixin, DeviceFKMixin, UserConsumableFKMixin

if TYPE_CHECKING:
    from app.models.objects.user import User
    from app.models.objects.device import Device
    from app.models.events_logs.user_consumable import UserConsumable

class ConsumableUsageLog(Base, TimestampMixin, LogBaseMixin, UserFKMixin, DeviceFKMixin, UserConsumableFKMixin):
    """
    [Log] 소모품 사용 로그 모델:
    특정 사용자가 특정 장치에서 소모품을 사용한 기록을 저장합니다.
    """
    __tablename__ = "consumable_usage_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    usage_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    quantity_used: Mapped[float] = mapped_column(Float, nullable=False)
    
    event_type: Mapped[str] = mapped_column(
        Enum('DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', 'SERVER_MQTT_CERTIFICATE_ISSUED', 
            'DEVICE_CERTIFICATE_CREATED', 'CERTIFICATE_REVOKED', 
            'SERVER_CERTIFICATE_ACQUIRED_NEW', 
            name='consumable_log_event_type', # 고유한 이름 부여
            create_type=False), 
        nullable=False, 
        default='CONSUMABLE_USAGE'
    )

    # --- Relationships ---
    user: Mapped["User"] = relationship(
        "User", back_populates="consumable_usage_log_entries"
    )
    device: Mapped["Device"] = relationship(
        "Device", back_populates="consumable_usage_logs"
    )
    user_consumable: Mapped["UserConsumable"] = relationship(
        "UserConsumable", back_populates="usage_logs"
    )