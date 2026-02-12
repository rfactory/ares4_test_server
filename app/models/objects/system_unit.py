import enum
from sqlalchemy import BigInteger, String, Enum, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, NullableOrganizationFKMixin, ProductLineFKMixin, NullableUserFKMixin

if TYPE_CHECKING:
    from app.models.objects.product_line import ProductLine
    from app.models.objects.organization import Organization
    from app.models.objects.user import User
    from app.models.objects.device import Device
    from app.models.events_logs.telemetry_data import TelemetryData
    from app.models.events_logs.unit_activity_log import UnitActivityLog
    from app.models.objects.action_log import ActionLog
    from app.models.objects.vision_feature import VisionFeature
    from app.models.objects.image_registry import ImageRegistry
    from app.models.relationships.organization_subscription import OrganizationSubscription
    from app.models.relationships.user_subscription import UserSubscription
    from app.models.relationships.alert_rule import AlertRule
    from app.models.internal.internal_system_unit_physical_component import InternalSystemUnitPhysicalComponent
    from app.models.relationships.schedule import Schedule
    from app.models.relationships.trigger_rule import TriggerRule
    from app.models.relationships.device_role_assignment import DeviceRoleAssignment
    from app.models.events_logs.observation_snapshot import ObservationSnapshot

# 1. 유닛 운영 상태 관리를 위한 Enum
class UnitStatus(str, enum.Enum):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    MAINTENANCE = 'MAINTENANCE'
    PROVISIONING = 'PROVISIONING'

class SystemUnit(Base, TimestampMixin, NullableOrganizationFKMixin, ProductLineFKMixin, NullableUserFKMixin):
    """
    [Object] 시스템 유닛 (The Hub):
    Ares4 시스템의 모든 데이터와 로직이 집약되는 최상위 운영 단위입니다.
    개별 장치를 클러스터링하고, AI 에이전트가 상태를 관측(Snapshot)하고 제어(Action)하는 기준점이 됩니다.
    """
    __tablename__ = "system_units"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    master_device_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        ForeignKey("devices.id", ondelete="SET NULL"), 
        nullable=True,
        comment="클러스터의 텔레메트리 전송을 담당하는 마스터 기기"
    )
    
    # 운영 상태 (Enum 적용)
    status: Mapped[UnitStatus] = mapped_column(
        Enum(UnitStatus, name='unit_status', create_type=False),
        default=UnitStatus.PROVISIONING,
        nullable=False
    )
    
    # 2. 지능형 제어 로직 (스케줄 및 트리거)
    schedules: Mapped[List["Schedule"]] = relationship(
        "Schedule", back_populates="system_unit", cascade="all, delete-orphan"
    )
    trigger_rules: Mapped[List["TriggerRule"]] = relationship(
        "TriggerRule", back_populates="system_unit", cascade="all, delete-orphan"
    )

    # 유닛별 가변 설정 (목표 온도, 가동 시간 등)
    unit_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Relationships ---
    
    # 1. 소속 및 정체성 (Top-Down 계층 구조 연결)
    product_line: Mapped["ProductLine"] = relationship("ProductLine", back_populates="system_units")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="system_units")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="system_units")

    # 2. 하부 구조 (물리적 실체)
    # [신하] 유닛에 소속된 컴퓨팅 노드들
    devices: Mapped[List["Device"]] = relationship(
        "Device", 
        back_populates="system_unit",
        foreign_keys="[Device.system_unit_id]" 
    )
    master_device: Mapped[Optional["Device"]] = relationship(
        "Device", 
        foreign_keys=[master_device_id]
    )
    
    role_assignments: Mapped[List["DeviceRoleAssignment"]] = relationship(
        "DeviceRoleAssignment", 
        back_populates="system_unit",
        cascade="all, delete-orphan"
    )
    
    # [As-Built] 실제 조립된 물리 부품 리스트 (BOM 실물 버전)
    physical_components: Mapped[List["InternalSystemUnitPhysicalComponent"]] = relationship(
        "InternalSystemUnitPhysicalComponent",
        back_populates="system_unit",
        cascade="all, delete-orphan"
    )
    
    # 3. 데이터 피드백 루프 (AI/RL의 핵심)
    telemetry_data: Mapped[List["TelemetryData"]] = relationship("TelemetryData", back_populates="system_unit")
    unit_activities: Mapped[List["UnitActivityLog"]] = relationship("UnitActivityLog", back_populates="system_unit")
    action_logs: Mapped[List["ActionLog"]] = relationship("ActionLog", back_populates="system_unit")
    vision_features: Mapped[List["VisionFeature"]] = relationship("VisionFeature", back_populates="system_unit")
    image_registries: Mapped[List["ImageRegistry"]] = relationship("ImageRegistry", back_populates="system_unit")
    observation_snapshots: Mapped[List["ObservationSnapshot"]] = relationship("ObservationSnapshot", back_populates="system_unit",cascade="all, delete-orphan")

    # 4. 비즈니스 가드레일
    subscription: Mapped[Optional["OrganizationSubscription"]] = relationship(
        "OrganizationSubscription", back_populates="system_unit", uselist=False
    )
    user_subscription: Mapped[Optional["UserSubscription"]] = relationship(
        "UserSubscription", back_populates="system_unit", uselist=False
    )
    alert_rules: Mapped[List["AlertRule"]] = relationship("AlertRule", back_populates="system_unit")

    def __repr__(self):
        return f"<SystemUnit(id={self.id}, name={self.name}, master={self.master_device_id}, status={self.status})>"