import enum
from sqlalchemy import BigInteger, String, Enum, JSON, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, ProductLineFKMixin

if TYPE_CHECKING:
    from app.models.objects.product_line import ProductLine
    from app.models.objects.device import Device
    from app.models.relationships.system_unit_assignment import SystemUnitAssignment
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
    from app.models.objects.provisioning_token import ProvisioningToken

class UnitStatus(str, enum.Enum):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    MAINTENANCE = 'MAINTENANCE'
    PROVISIONING = 'PROVISIONING'

class SystemUnit(Base, TimestampMixin, ProductLineFKMixin):
    """
    [Object] 시스템 유닛 (The Hub):
    Ares4 시스템의 모든 데이터와 로직이 집약되는 최상위 운영 단위입니다.
    [변경사항] 소유권 관계를 직접 FK에서 SystemUnitAssignment 브릿지 테이블로 이전했습니다.
    """
    __tablename__ = "system_units"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 클러스터 마스터 (Nullable: 아직 기기가 할당되지 않은 유닛 상태 고려)
    master_device_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        ForeignKey("devices.id", ondelete="SET NULL"), 
        nullable=True,
        comment="클러스터의 텔레메트리 전송을 담당하는 마스터 기기"
    )
    
    status: Mapped[UnitStatus] = mapped_column(
        Enum(UnitStatus, name='unit_status', create_type=False),
        default=UnitStatus.PROVISIONING,
        nullable=False
    )
    
    # 가변 설정 및 설명
    unit_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Relationships ---
    
    # 1. 소유권 및 권한 (핵심 변경 포인트)
    # 이제 이 유닛의 주인 정보는 assignments 리스트에서 OWNER 역할을 찾아서 결정합니다.
    assignments: Mapped[List["SystemUnitAssignment"]] = relationship(
        "SystemUnitAssignment", 
        back_populates="system_unit",
        cascade="all, delete-orphan"
    )
    
    # [정리] 직접 관계는 물리적/법적 소속 정보 조회용으로만 유지 (Optional)
    product_line: Mapped["ProductLine"] = relationship("ProductLine", back_populates="system_units")

    # 2. 하부 구조 (하드웨어 클러스터)
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
        "DeviceRoleAssignment", back_populates="system_unit", cascade="all, delete-orphan"
    )
    
    physical_components: Mapped[List["InternalSystemUnitPhysicalComponent"]] = relationship(
        "InternalSystemUnitPhysicalComponent", back_populates="system_unit", cascade="all, delete-orphan"
    )
    
    # 3. 운영 및 지능형 로직
    schedules: Mapped[List["Schedule"]] = relationship(
        "Schedule", back_populates="system_unit", cascade="all, delete-orphan"
    )
    trigger_rules: Mapped[List["TriggerRule"]] = relationship(
        "TriggerRule", back_populates="system_unit", cascade="all, delete-orphan"
    )
    alert_rules: Mapped[List["AlertRule"]] = relationship(
        "AlertRule", back_populates="system_unit"
    )
    
    # 4. 데이터 피드백 루프
    telemetry_data: Mapped[List["TelemetryData"]] = relationship("TelemetryData", back_populates="system_unit")
    unit_activities: Mapped[List["UnitActivityLog"]] = relationship("UnitActivityLog", back_populates="system_unit")
    action_logs: Mapped[List["ActionLog"]] = relationship("ActionLog", back_populates="system_unit")
    vision_features: Mapped[List["VisionFeature"]] = relationship("VisionFeature", back_populates="system_unit")
    image_registries: Mapped[List["ImageRegistry"]] = relationship("ImageRegistry", back_populates="system_unit")
    observation_snapshots: Mapped[List["ObservationSnapshot"]] = relationship(
        "ObservationSnapshot", back_populates="system_unit", cascade="all, delete-orphan"
    )

    # 5. 프로비저닝 및 비즈니스
    provisioning_token: Mapped[Optional["ProvisioningToken"]] = relationship(
        "ProvisioningToken", 
        back_populates="system_unit", 
        uselist=False, # 이 설정이 있어야 1:1 관계가 성립합니다.
        cascade="all, delete-orphan"
    )
    subscription: Mapped[Optional["OrganizationSubscription"]] = relationship(
        "OrganizationSubscription", back_populates="system_unit", uselist=False
    )
    user_subscription: Mapped[Optional["UserSubscription"]] = relationship(
        "UserSubscription", back_populates="system_unit", uselist=False
    )

    def __repr__(self):
        return f"<SystemUnit(id={self.id}, name={self.name}, status={self.status})>"