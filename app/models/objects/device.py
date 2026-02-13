from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Enum, Index, Boolean, Integer, Uuid, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import enum
import uuid

from app.database import Base
from ..base_model import TimestampMixin, NullableHardwareBlueprintFKMixin, NullableSystemUnitFKMixin

if TYPE_CHECKING:
    from app.models.objects.user import User
    from app.models.objects.organization import Organization
    from app.models.objects.system_unit import SystemUnit
    from app.models.relationships.device_role_assignment import DeviceRoleAssignment
    from app.models.relationships.device_component_instance import DeviceComponentInstance
    from app.models.relationships.device_component_pin_mapping import DeviceComponentPinMapping
    from app.models.relationships.alert_rule import AlertRule
    from app.models.events_logs.telemetry_data import TelemetryData
    from app.models.events_logs.device_log import DeviceLog
    from app.models.events_logs.unit_activity_log import UnitActivityLog
    from app.models.events_logs.firmware_update import FirmwareUpdate
    from app.models.objects.image_registry import ImageRegistry
    from app.models.objects.vision_feature import VisionFeature
    from app.models.objects.action_log import ActionLog
    from app.models.events_logs.alert_event import AlertEvent
    from app.models.events_logs.consumable_usage_log import ConsumableUsageLog
    from app.models.events_logs.batch_tracking import BatchTracking
    from app.models.objects.hardware_blueprint import HardwareBlueprint

# --- Enum 정의 (동일) ---
class DeviceVisibilityEnum(str, enum.Enum):
    PRIVATE = 'PRIVATE'
    ORGANIZATION = 'ORGANIZATION'
    PUBLIC = 'PUBLIC'

class ClusterRoleEnum(str, enum.Enum):
    LEADER = "LEADER"
    FOLLOWER = "FOLLOWER"

class DeviceStatusEnum(str, enum.Enum):
    PENDING = "PENDING"          # 공장 출고 후 대기 (블루투스 페어링 전)
    CLAIMED = "CLAIMED"          # 블루투스로 사용자가 '내 기기'로 찜한 상태 (유닛 할당 전)
    PROVISIONED = "PROVISIONED"  # 유닛 할당 및 설정 완료 (정식 가동 중)
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    TIMEOUT = "TIMEOUT"
    RECOVERY_NEEDED = "RECOVERY_NEEDED"
    SAFETY_LOCKED = "SAFETY_LOCKED"
    BLOCKED = "BLOCKED"

class Device(Base, TimestampMixin, NullableHardwareBlueprintFKMixin, NullableSystemUnitFKMixin):
    """
    [Object] 장치 마스터 모델:
    [변경사항] 
    1. 하드웨어 점유(Claim)를 위해 owner_user_id, owner_organization_id 필드 도입.
    2. DB 레벨에서 개인/조직 상호 배타적 소유권(XOR) 강제.
    3. 유닛 할당(system_unit_id)은 수동 프로세스를 위해 Nullable 유지.
    """
    __tablename__ = "devices"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    cpu_serial: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    current_uuid: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False, index=True, default=uuid.uuid4)
    
    # 하드웨어 점유 정보 (유닛 할당 전 '가방 속 기기' 관리용)
    owner_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True, index=True)
    owner_organization_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # 보안 및 신원
    hmac_key_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    hmac_secret_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    visibility_status: Mapped[DeviceVisibilityEnum] = mapped_column(
        Enum(DeviceVisibilityEnum, name='device_visibility', create_type=False), 
        default=DeviceVisibilityEnum.PRIVATE, nullable=False
    )
    status: Mapped[DeviceStatusEnum] = mapped_column(
        Enum(DeviceStatusEnum, name='device_status', create_type=False), 
        default=DeviceStatusEnum.PENDING, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # 클러스터링 및 관리 로직
    cluster_role: Mapped[ClusterRoleEnum] = mapped_column(
        Enum(ClusterRoleEnum, name='cluster_role', create_type=False),
        default=ClusterRoleEnum.FOLLOWER
    )
    logical_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 하드웨어 교체 이력 (Self-reference)
    replaced_from_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("devices.id"), nullable=True)
    
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    recovery_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    recovery_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        # DB 단계에서 XOR 강제
        # "유저가 있으면 조직은 없어야 하고, 조직이 있으면 유저는 없어야 함. 둘 다 없는 PENDING은 허용"
        CheckConstraint(
            "(owner_user_id IS NOT NULL AND owner_organization_id IS NULL) OR "
            "(owner_user_id IS NULL AND owner_organization_id IS NOT NULL) OR "
            "(owner_user_id IS NULL AND owner_organization_id IS NULL)",
            name="check_exclusive_device_owner"
        ),
    )
    
    # --- Relationships ---
    
    # 1. 소유권 관계 (Inventory)
    owner_user: Mapped[Optional["User"]] = relationship("User", back_populates="owned_devices")
    owner_organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="owned_devices")
    
    # 2. 인프라 관계 (Deployment)
    # NullableSystemUnitFKMixin에서 system_unit_id를 가져오므로, 여기서는 할당된 유닛과의 관계 정의
    system_unit: Mapped[Optional["SystemUnit"]] = relationship("SystemUnit", back_populates="devices")
        
    # 3. 설계 및 역할
    hardware_blueprint: Mapped["HardwareBlueprint"] = relationship("HardwareBlueprint", back_populates="devices")
    replaced_from: Mapped[Optional["Device"]] = relationship("Device", remote_side=[id])
    
    role_assignments: Mapped[List["DeviceRoleAssignment"]] = relationship("DeviceRoleAssignment", back_populates="device")
    component_instances: Mapped[List["DeviceComponentInstance"]] = relationship("DeviceComponentInstance", back_populates="device")
    pin_mappings: Mapped[List["DeviceComponentPinMapping"]] = relationship(
        "DeviceComponentPinMapping", 
        back_populates="device",
        cascade="all, delete-orphan"
    )
    
    # 4. 데이터 및 로그 (기존 유지)
    telemetry_data: Mapped[List["TelemetryData"]] = relationship("TelemetryData", back_populates="device")
    unit_activities: Mapped[List["UnitActivityLog"]] = relationship("UnitActivityLog", back_populates="device")
    device_logs: Mapped[List["DeviceLog"]] = relationship("DeviceLog", back_populates="device")
    alert_events: Mapped[List["AlertEvent"]] = relationship("AlertEvent", back_populates="device")
    alert_rules: Mapped[List["AlertRule"]] = relationship("AlertRule", back_populates="device")
    batch_trackings: Mapped[List["BatchTracking"]] = relationship("BatchTracking", back_populates="device", cascade="all, delete-orphan")
    
    image_registries: Mapped[List["ImageRegistry"]] = relationship("ImageRegistry", back_populates="device")
    vision_features: Mapped[List["VisionFeature"]] = relationship("VisionFeature", back_populates="device")
    action_logs: Mapped[List["ActionLog"]] = relationship("ActionLog", back_populates="device")
    
    consumable_usage_logs: Mapped[List["ConsumableUsageLog"]] = relationship("ConsumableUsageLog", back_populates="device")
    firmware_updates: Mapped[List["FirmwareUpdate"]] = relationship("FirmwareUpdate", back_populates="device")