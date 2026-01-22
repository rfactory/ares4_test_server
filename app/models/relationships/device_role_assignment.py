# app/models/relationships/device_role_assignment.py
from sqlalchemy import BigInteger, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING # Optional, TYPE_CHECKING 추가
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, SystemUnitFKMixin

# 런타임 순환 참조 방지 및 타입 힌트 지원
if TYPE_CHECKING:
    from app.models.objects.device import Device
    from app.models.objects.device_role import DeviceRole
    from app.models.objects.system_unit import SystemUnit

class DeviceRoleAssignment(Base, TimestampMixin, DeviceFKMixin, SystemUnitFKMixin):
    """
    [Relationship] 특정 SystemUnit(클러스터) 내에서 기기(Device)에게 부여된 역할(Role)을 관리합니다.
    기기와 역할, 그리고 소속 유닛을 연결하는 핵심 맵핑 테이블입니다.
    """
    __tablename__ = "device_role_assignments"
    __table_args__ = (
        # 동일 유닛 내에서 한 기기가 동일한 역할을 중복해서 가질 수 없도록 제한
        UniqueConstraint('device_id', 'role_id', 'system_unit_id', name='_device_role_unit_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 역할 정보 연결
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("device_roles.id"), nullable=False)
    
    # 역할 활성화 상태 (역할을 삭제하지 않고 잠시 끄고 켤 때 유용)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- 외래 키 ---
    # device_id는 DeviceFKMixin으로부터 상속
    # system_unit_id는 SystemUnitFKMixin으로부터 상속

    # --- Relationships ---
    device: Mapped["Device"] = relationship("Device", back_populates="role_assignments")
    role: Mapped["DeviceRole"] = relationship("DeviceRole", back_populates="assignments")
    system_unit: Mapped["SystemUnit"] = relationship("SystemUnit") # 유닛별 역할 조회를 위해 연결
