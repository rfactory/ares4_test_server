# app/models/events_logs/firmware_update.py
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from datetime import datetime # Added datetime

from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, HardwareBlueprintFKMixin

if TYPE_CHECKING:
    from app.models.objects.user import User
    from app.models.objects.device import Device
    from app.models.objects.hardware_blueprint import HardwareBlueprint
    from app.models.objects.organization import Organization


class FirmwareUpdate(Base, TimestampMixin, DeviceFKMixin, HardwareBlueprintFKMixin):
    """
    펌웨어 업데이트 모델은 장치에 대한 펌웨어 업데이트 기록을 저장합니다.
    이는 장치 유지보수 및 버전 관리에 사용됩니다.
    """
    __tablename__ = "firmware_updates"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 펌웨어 업데이트 기록의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다. (BigInteger)
    # hardware_blueprint_id는 HardwareBlueprintFKMixin으로부터 상속받습니다. (BigInteger)
    firmware_version: Mapped[str] = mapped_column(String(50), nullable=False) # 업데이트된 펌웨어의 버전
    update_status: Mapped[str] = mapped_column(Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'ROLLBACK', name='update_status', create_type=False), default='PENDING', nullable=False) # 펌웨어 업데이트의 현재 상태 ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'ROLLBACK')
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False) # 펌웨어 업데이트가 시작된 시간
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) # 펌웨어 업데이트가 완료된 시간

    # 명시적으로 외래 키 컬럼 정의
    initiated_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True) # 펌웨어 업데이트를 시작한 사용자 ID
    initiated_by_organization_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey('organizations.id'), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 펌웨어 업데이트에 대한 추가 메모

    # --- Relationships ---
    device: Mapped["Device"] = relationship("Device", back_populates="firmware_updates") # 펌웨어 업데이트가 적용된 장치 정보
    hardware_blueprint: Mapped["HardwareBlueprint"] = relationship("HardwareBlueprint", back_populates="firmware_updates") # 이 펌웨어 업데이트가 적용되는 하드웨어 블루프린트 정보
    initiated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[initiated_by_user_id], back_populates="firmware_updates_initiated") # 펌웨어 업데이트를 시작한 사용자 정보
    organization: Mapped[Optional["Organization"]] = relationship("Organization", foreign_keys=[initiated_by_organization_id], back_populates="firmware_updates")