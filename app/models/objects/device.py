from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Enum, Index, Boolean, Integer, Uuid
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import enum
import uuid

from app.database import Base
from ..base_model import TimestampMixin, NullableHardwareBlueprintFKMixin, NullableSystemUnitFKMixin

if TYPE_CHECKING:
    from app.models.objects.system_unit import SystemUnit
    from app.models.relationships.device_role_assignment import DeviceRoleAssignment
    from app.models.events_logs.unit_activity_log import UnitActivityLog
    from app.models.objects.hardware_blueprint import HardwareBlueprint
    from app.models.relationships.organization_device import OrganizationDevice
    from app.models.relationships.device_component_instance import DeviceComponentInstance
    from app.models.relationships.user_device import UserDevice
    from app.models.relationships.alert_rule import AlertRule
    from app.models.events_logs.telemetry_data import TelemetryData
    from app.models.events_logs.device_log import DeviceLog
    from app.models.events_logs.firmware_update import FirmwareUpdate
    from app.models.objects.image_registry import ImageRegistry
    from app.models.objects.vision_feature import VisionFeature
    from app.models.objects.action_log import ActionLog
    from app.models.events_logs.alert_event import AlertEvent
    from app.models.events_logs.consumable_usage_log import ConsumableUsageLog
    from app.models.objects.provisioning_token import ProvisioningToken
    from app.models.events_logs.batch_tracking import BatchTracking

# 1. 시인성 및 상태 관리를 위한 Enum 정의 추가
class DeviceVisibilityEnum(str, enum.Enum):
    PRIVATE = 'PRIVATE'
    ORGANIZATION = 'ORGANIZATION'
    PUBLIC = 'PUBLIC'

class ClusterRoleEnum(str, enum.Enum):
    LEADER = "LEADER"
    FOLLOWER = "FOLLOWER"

class DeviceStatusEnum(str, enum.Enum):
    PENDING = "PENDING" 
    PROVISIONED = "PROVISIONED" 
    ONLINE = "ONLINE" 
    OFFLINE = "OFFLINE" 
    TIMEOUT = "TIMEOUT" 
    RECOVERY_NEEDED = "RECOVERY_NEEDED" 
    SAFETY_LOCKED = "SAFETY_LOCKED" 
    BLOCKED = "BLOCKED" 

class Device(Base, TimestampMixin, NullableHardwareBlueprintFKMixin, NullableSystemUnitFKMixin):
    """
    [Object] 장치 마스터 모델:
    하드웨어 식별 정보, 실시간 통신 상태, 그리고 모든 이벤트 로그를 연결하는 시스템의 핵심 허브입니다.
    """
    __tablename__ = "devices"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    cpu_serial: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    current_uuid: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False, index=True, default=uuid.uuid4)
    
    # 보안 및 신원 (Enum 적용)
    hmac_key_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    visibility_status: Mapped[DeviceVisibilityEnum] = mapped_column(
        Enum(DeviceVisibilityEnum, name='device_visibility', create_type=False), 
        default=DeviceVisibilityEnum.PRIVATE, nullable=False
    )
    hmac_secret_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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
    
    # 자기 참조 관계: 이전 장치로부터 교체되었을 경우 (Hardware Lifecycle)
    replaced_from_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("devices.id"), nullable=True)
    
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    recovery_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    recovery_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # --- Relationships ---

    # 0. 보안 및 자기 참조
    provisioning_token: Mapped[Optional["ProvisioningToken"]] = relationship(
        "ProvisioningToken", back_populates="device", uselist=False
    )
    replaced_from: Mapped[Optional["Device"]] = relationship("Device", remote_side=[id])
    
    # 1. 인프라 관계
    system_unit: Mapped["SystemUnit"] = relationship("SystemUnit", back_populates="devices")
    organization_devices: Mapped[List["OrganizationDevice"]] = relationship("OrganizationDevice", back_populates="device")
    users: Mapped[List["UserDevice"]] = relationship("UserDevice", back_populates="device")
    
    # 2. 설계 및 역할
    hardware_blueprint: Mapped["HardwareBlueprint"] = relationship("HardwareBlueprint", back_populates="devices")
    role_assignments: Mapped[List["DeviceRoleAssignment"]] = relationship("DeviceRoleAssignment", back_populates="device")
    component_instances: Mapped[List["DeviceComponentInstance"]] = relationship("DeviceComponentInstance", back_populates="device")
    
    # 3. 데이터 및 AI (우리가 이전에 다듬은 모델들)
    image_registries: Mapped[List["ImageRegistry"]] = relationship("ImageRegistry", back_populates="device")
    vision_features: Mapped[List["VisionFeature"]] = relationship("VisionFeature", back_populates="device")
    action_logs: Mapped[List["ActionLog"]] = relationship("ActionLog", back_populates="device")
    
    # 4. 모니터링 및 로그
    telemetry_data: Mapped[List["TelemetryData"]] = relationship("TelemetryData", back_populates="device")
    unit_activities: Mapped[List["UnitActivityLog"]] = relationship("UnitActivityLog", back_populates="device")
    device_logs: Mapped[List["DeviceLog"]] = relationship("DeviceLog", back_populates="device")
    alert_events: Mapped[List["AlertEvent"]] = relationship("AlertEvent", back_populates="device")
    alert_rules: Mapped[List["AlertRule"]] = relationship("AlertRule", back_populates="device")
    batch_trackings: Mapped[List["BatchTracking"]] = relationship("BatchTracking", back_populates="device",cascade="all, delete-orphan")    
    # 5. 소모품 및 업데이트
    consumable_usage_logs: Mapped[List["ConsumableUsageLog"]] = relationship("ConsumableUsageLog", back_populates="device")
    firmware_updates: Mapped[List["FirmwareUpdate"]] = relationship("FirmwareUpdate", back_populates="device")