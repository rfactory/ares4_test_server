import enum # Python Enum 추가
from sqlalchemy import BigInteger, DateTime, JSON, Enum, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.sql import func

from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, UserFKMixin, NullableSystemUnitFKMixin

if TYPE_CHECKING:
    from app.models.objects.device import Device
    from app.models.objects.user import User
    from app.models.objects.system_unit import SystemUnit

# 코드 가독성과 재사용성을 위한 Python Enum 클래스
class ActivityType(str, enum.Enum):
    OPERATION = 'OPERATION'
    INFERENCE = 'INFERENCE'
    MAINTENANCE = 'MAINTENANCE'
    SYSTEM_EVENT = 'SYSTEM_EVENT'

class UnitActivityLog(Base, TimestampMixin, DeviceFKMixin, UserFKMixin, NullableSystemUnitFKMixin):
    __tablename__ = "unit_activity_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # Mapped[ActivityType]으로 지정하면 IDE에서 .value 자동 완성이 지원됩니다.
    activity_type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType, name='unit_activity_type', create_type=False), 
        nullable=False, 
        index=True
    )

    activity_payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Relationships (정의하신 대로 유지하되 Mapped 명시) ---
    device: Mapped["Device"] = relationship("Device", back_populates="unit_activities")
    user: Mapped["User"] = relationship("User", back_populates="unit_activities")
    system_unit: Mapped[Optional["SystemUnit"]] = relationship("SystemUnit", back_populates="unit_activities")