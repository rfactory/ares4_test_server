from sqlalchemy import BigInteger, DateTime, JSON, Enum, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.sql import func

from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, UserFKMixin, NullableSystemUnitFKMixin # SystemUnitFKMixin 추가

if TYPE_CHECKING:
    from app.models.objects.device import Device
    from app.models.objects.user import User
    from app.models.objects.system_unit import SystemUnit


class UnitActivityLog(Base, TimestampMixin, DeviceFKMixin, UserFKMixin, NullableSystemUnitFKMixin):
    """
    [Universal Log] 유닛 활동 로그
    특정 시스템 유닛 또는 장치에서 발생한 모든 유의미한 활동(운영, 추론, 유지보수)을 통합 기록합니다.
    도메인에 종속되지 않고 JSON 페이로드를 통해 확장성을 보장합니다.
    """
    __tablename__ = "unit_activity_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # device_id, user_id는 Mixin으로부터 상속받음
    # system_unit_id는 NullableSystemUnitFKMixin으로부터 상속받음 (optional)
    
    # 활동 유형: 운영(수확 등), AI추론, 유지보수, 시스템상태 변경 등
    activity_type: Mapped[str] = mapped_column(
        Enum('OPERATION', 'INFERENCE', 'MAINTENANCE', 'SYSTEM_EVENT', name='unit_activity_type'), 
        nullable=False, 
        index=True
    )

    # 핵심 데이터: 각 타입에 맞는 상세 데이터를 JSON으로 저장
    # 예: {"yield": 5.2}, {"bounding_boxes": [...]}, {"replaced_part_id": 101}
    activity_payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # 활동 발생 시간
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Relationships ---
    device: Mapped["Device"] = relationship("Device", back_populates="unit_activities") # Device 모델에 관계 추가 필요
    user: Mapped["User"] = relationship("User", back_populates="unit_activities") # User 모델에 관계 추가 필요
    system_unit: Mapped[Optional["SystemUnit"]] = relationship("SystemUnit", back_populates="unit_activities") # SystemUnit 모델에 관계 추가 필요