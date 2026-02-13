from sqlalchemy import BigInteger, String, DateTime, Boolean, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    # 1. 인벤토리 및 할당
    from app.models.objects.device import Device
    from app.models.relationships.system_unit_assignment import SystemUnitAssignment
    
    # 2. IAM 및 권한 체계
    from app.models.relationships.user_organization_role import UserOrganizationRole
    from app.models.objects.access_request import AccessRequest
    
    # 3. 자동화 및 모니터링 (공유 기능)
    from app.models.relationships.schedule import Schedule
    from app.models.relationships.alert_rule import AlertRule
    from app.models.relationships.trigger_rule import TriggerRule
    
    # 4. 운영 로그 및 데이터 (공유 기능)
    from app.models.events_logs.audit_log import AuditLog
    from app.models.objects.action_log import ActionLog
    from app.models.events_logs.unit_activity_log import UnitActivityLog
    from app.models.events_logs.alert_event import AlertEvent
    from app.models.events_logs.consumable_usage_log import ConsumableUsageLog

    # 5. 시스템 유지보수 및 보안 (공유 기능)
    from app.models.events_logs.firmware_update import FirmwareUpdate
    from app.models.objects.provisioning_token import ProvisioningToken
    from app.models.objects.refresh_token import RefreshToken

    # 6. 비즈니스 및 구독
    from app.models.relationships.user_subscription import UserSubscription
    from app.models.events_logs.user_consumable import UserConsumable

    # 7. 내부 자산 관리 (MP3 제조사 재고 관리 대응)
    from app.models.internal.internal_asset_inventory import InternalAssetInventory
    from app.models.internal.internal_asset_purchase_record import InternalAssetPurchaseRecord
    
class User(Base, TimestampMixin):
    """
    [Object] 사용자 모델:
    Ares4 시스템의 모든 활동 주체입니다. 
    계정 정보, 인증 상태, 그리고 인프라/자산/보안과 관련된 방대한 관계를 관리합니다.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 인증 및 보안 상태
    last_login: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_verification_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # --- Relationships (Mapped 적용 완료) ---
    
    # 1. 운영 및 활동 로그
    unit_activities: Mapped[List["UnitActivityLog"]] = relationship("UnitActivityLog", back_populates="user")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user")
    action_logs: Mapped[List["ActionLog"]] = relationship(
        "ActionLog", foreign_keys="[ActionLog.user_id]", back_populates="performed_by_user"
    )

    # 2. RBAC 권한 및 요청 관리 (1:N 다중 관계 처리)
    user_role_assignments: Mapped[List["UserOrganizationRole"]] = relationship("UserOrganizationRole", back_populates="user")
    
    access_requests_for_user: Mapped[List["AccessRequest"]] = relationship(
        "AccessRequest", foreign_keys="[AccessRequest.user_id]", back_populates="user"
    )
    reviewed_access_requests: Mapped[List["AccessRequest"]] = relationship(
        "AccessRequest", foreign_keys="[AccessRequest.reviewed_by_user_id]", back_populates="reviewed_by"
    )
    initiated_invitations: Mapped[List["AccessRequest"]] = relationship(
        "AccessRequest", foreign_keys="[AccessRequest.initiated_by_user_id]", back_populates="initiated_by"
    )

    
    subscriptions: Mapped[List["UserSubscription"]] = relationship("UserSubscription", back_populates="user")
    user_consumables: Mapped[List["UserConsumable"]] = relationship("UserConsumable", back_populates="user")
    
    # 4. 자동화 및 경보 제어
    schedules: Mapped[List["Schedule"]] = relationship("Schedule", back_populates="user")
    alert_rules: Mapped[List["AlertRule"]] = relationship("AlertRule", back_populates="user")
    trigger_rules: Mapped[List["TriggerRule"]] = relationship("TriggerRule", back_populates="user")
    
    alert_events_generated: Mapped[List["AlertEvent"]] = relationship(
        "AlertEvent", foreign_keys="[AlertEvent.user_id]", back_populates="user"
    )
    alert_events_acknowledged: Mapped[List["AlertEvent"]] = relationship(
        "AlertEvent", foreign_keys="[AlertEvent.acknowledged_by_user_id]", back_populates="acknowledged_by_user"
    )

    # 5. 시스템 및 보안 자산
    firmware_updates_initiated: Mapped[List["FirmwareUpdate"]] = relationship(
        "FirmwareUpdate", foreign_keys="[FirmwareUpdate.initiated_by_user_id]", back_populates="initiated_by_user"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user")
    consumable_usage_log_entries: Mapped[List["ConsumableUsageLog"]] = relationship("ConsumableUsageLog", back_populates="user")
    issued_provisioning_tokens: Mapped[List["ProvisioningToken"]] = relationship(
        "ProvisioningToken",
        back_populates="issued_by_user",
        cascade="all, delete-orphan"
    )
    owned_devices: Mapped[List["Device"]] = relationship(
        "Device", 
        back_populates="owner_user",
        cascade="all, delete-orphan"
    )
    system_unit_assignments: Mapped[List["SystemUnitAssignment"]] = relationship(
        "SystemUnitAssignment", 
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # 6. 내부 자산 관리 (Inventory & Purchase)
    internal_asset_inventory_updates: Mapped[List["InternalAssetInventory"]] = relationship(
        "InternalAssetInventory", 
        foreign_keys="[InternalAssetInventory.last_updated_by_user_id]", 
        back_populates="last_updated_by_user"
    )
    internal_asset_purchase_records: Mapped[List["InternalAssetPurchaseRecord"]] = relationship(
        "InternalAssetPurchaseRecord", 
        foreign_keys="[InternalAssetPurchaseRecord.recorded_by_user_id]", 
        back_populates="recorded_by_user"
    )

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"