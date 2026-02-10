from sqlalchemy import BigInteger, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, SystemUnitFKMixin

if TYPE_CHECKING:
    from app.models.objects.device import Device
    from app.models.objects.device_role import DeviceRole
    from app.models.objects.system_unit import SystemUnit

class DeviceRoleAssignment(Base, TimestampMixin, DeviceFKMixin, SystemUnitFKMixin):
    """
    [Relationship] 기기 역할 할당 모델:
    특정 SystemUnit(클러스터) 내에서 기기(Device)가 수행할 구체적인 역할을 정의합니다.
    예: 기기 A는 클러스터 1에서 '메인 센서 노드'이자 '게이트웨이' 역할을 수행.
    """
    __tablename__ = "device_role_assignments"
    __table_args__ = (
        # 동일 유닛 내에서 장치와 역할의 조합 중복 방지
        UniqueConstraint('device_id', 'role_id', 'system_unit_id', name='_device_role_unit_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 부여된 역할 (예: LEADER, FOLLOWER, MONITOR)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("device_roles.id"), nullable=False)
    
    # 역할의 일시적 활성화/비활성화
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships (Mapped 적용 완료) ---

    # 1. 대상 기기
    device: Mapped["Device"] = relationship(
        "Device", 
        back_populates="role_assignments"
    )
    
    # 2. 역할 정의
    role: Mapped["DeviceRole"] = relationship(
        "DeviceRole", 
        back_populates="assignments"
    )
    
    # 3. 소속 유닛 (클러스터 컨텍스트)
    system_unit: Mapped["SystemUnit"] = relationship(
        "SystemUnit",
        back_populates="role_assignments" # SystemUnit 모델에도 이 관계가 정의되어야 합니다.
    )

    def __repr__(self):
        return f"<DeviceRoleAssignment(device_id={self.device_id}, role_id={self.role_id}, active={self.is_active})>"