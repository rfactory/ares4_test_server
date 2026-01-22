# app/models/objects/device.py
from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Enum, UUID, Index, Boolean, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import enum

from app.database import Base
# SystemUnitFKMixin을 추가로 상속받습니다.
from ..base_model import TimestampMixin, HardwareBlueprintFKMixin, SystemUnitFKMixin

if TYPE_CHECKING:
    from app.models.objects.system_unit import SystemUnit
    from app.models.relationships.device_role_assignment import DeviceRoleAssignment
    from app.models.events_logs.unit_activity_log import UnitActivityLog
    from app.models.objects.hardware_blueprint import HardwareBlueprint
    from app.models.relationships.organization_device import OrganizationDevice
    from app.models.relationships.device_component_instance import DeviceComponentInstance
    from app.models.relationships.user_device import UserDevice
    from app.models.relationships.schedule import Schedule
    from app.models.relationships.alert_rule import AlertRule
    from app.models.relationships.trigger_rule import TriggerRule
    from app.models.events_logs.telemetry_data import TelemetryData
    from app.models.events_logs.device_log import DeviceLog
    from app.models.events_logs.firmware_update import FirmwareUpdate
    from app.models.objects.image_registry import ImageRegistry
    from app.models.objects.vision_feature import VisionFeature
    from app.models.objects.action_log import ActionLog
    from app.models.events_logs.alert_event import AlertEvent
    from app.models.events_logs.consumable_usage_log import ConsumableUsageLog

class DeviceStatusEnum(enum.Enum):
    UNKNOWN = "UNKNOWN"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    TIMEOUT = "TIMEOUT"
    RECOVERY_NEEDED = "RECOVERY_NEEDED" # 인증서 복구 필요 상태

class Device(Base, TimestampMixin, HardwareBlueprintFKMixin, SystemUnitFKMixin):
    """
    장치 모델은 시스템에 등록된 각 하드웨어 장치의 고유한 식별 정보와 상태를 관리합니다.
    이제 SystemUnitFKMixin을 통해 특정 클러스터(SystemUnit)의 일원으로 관리됩니다.
    """
    __tablename__ = "devices"
    
    # 1. PK를 BigInteger로 설정하여 시스템 전반의 타입 일관성을 유지합니다.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 장치의 고유 ID
    cpu_serial: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True) # 장치의 CPU 고유 시리얼 번호
    current_uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, index=True) # 장치에 할당된 현재 UUID
    hmac_key_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True) # Vault Transit Engine 키 이름
    
    # --- 관계 정의 (외래 키) ---
    # hardware_blueprint_id는 HardwareBlueprintFKMixin으로부터 상속받습니다.
    # system_unit_id는 SystemUnitFKMixin으로부터 상속받습니다.

    # --- 추가 속성 ---
    visibility_status: Mapped[str] = mapped_column(Enum('PRIVATE', 'ORGANIZATION', 'PUBLIC', name='device_visibility', create_type=False), default='PRIVATE', nullable=False) # 공개 범위
    status: Mapped[DeviceStatusEnum] = mapped_column(Enum(DeviceStatusEnum, name='device_status', create_type=False), default=DeviceStatusEnum.UNKNOWN, nullable=False) # 상태
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # 활성화 상태
    
    # --- 기록 ---
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) # 마지막 연결 시간

    # --- 인증서 복구용 ---
    recovery_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True) # 복구 토큰
    recovery_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) # 토큰 만료 시간
    
    # --- Relationships ---
    # 2. 신규 추가: 클러스터(SystemUnit)와의 관계 정의
    system_unit: Mapped["SystemUnit"] = relationship("SystemUnit", back_populates="devices")
    
    # 3. 신규 추가: 기기에 할당된 다중 역할(DeviceRole)과의 N:M 관계
    role_assignments: Mapped[List["DeviceRoleAssignment"]] = relationship("DeviceRoleAssignment", back_populates="device")
    users: Mapped[List["UserDevice"]] = relationship("UserDevice", back_populates="device")
    
    # 4. 데이터 자산 및 AI/RL 관련 관계 추가
    image_registries: Mapped[List["ImageRegistry"]] = relationship("ImageRegistry", back_populates="device")
    vision_features: Mapped[List["VisionFeature"]] = relationship("VisionFeature", back_populates="device")
    action_logs: Mapped[List["ActionLog"]] = relationship("ActionLog", back_populates="device")
    alert_events: Mapped[List["AlertEvent"]] = relationship("AlertEvent", back_populates="device")
    
    # 5. 로그 및 모니터링
    unit_activities: Mapped[List["UnitActivityLog"]] = relationship("UnitActivityLog", back_populates="device")
    telemetry_data: Mapped[List["TelemetryData"]] = relationship("TelemetryData", back_populates="device")
    device_logs: Mapped[List["DeviceLog"]] = relationship("DeviceLog", back_populates="device")
    consumable_usage_logs: Mapped[List["ConsumableUsageLog"]] = relationship("ConsumableUsageLog",back_populates="device")
    
    # 5. 운영 및 설정
    hardware_blueprint: Mapped["HardwareBlueprint"] = relationship("HardwareBlueprint", back_populates="devices")
    organization_devices: Mapped[List["OrganizationDevice"]] = relationship("OrganizationDevice", back_populates="device")
    component_instances: Mapped[List["DeviceComponentInstance"]] = relationship("DeviceComponentInstance", back_populates="device")
    schedules: Mapped[List["Schedule"]] = relationship("Schedule", back_populates="device")
    alert_rules: Mapped[List["AlertRule"]] = relationship("AlertRule", back_populates="device")
    trigger_rules: Mapped[List["TriggerRule"]] = relationship("TriggerRule", back_populates="device")
    firmware_updates: Mapped[List["FirmwareUpdate"]] = relationship("FirmwareUpdate", back_populates="device")
    