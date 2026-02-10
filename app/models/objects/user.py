from sqlalchemy import BigInteger, String, DateTime, Boolean, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    from app.models.objects.system_unit import SystemUnit
    from app.models.objects.action_log import ActionLog
    from app.models.events_logs.audit_log import AuditLog
    from app.models.events_logs.unit_activity_log import UnitActivityLog
    from app.models.relationships.user_organization_role import UserOrganizationRole
    from app.models.objects.access_request import AccessRequest
    from app.models.relationships.user_device import UserDevice
    from app.models.events_logs.user_consumable import UserConsumable
    from app.models.events_logs.consumable_usage_log import ConsumableUsageLog
    from app.models.relationships.user_subscription import UserSubscription
    from app.models.relationships.schedule import Schedule
    from app.models.relationships.alert_rule import AlertRule
    from app.models.relationships.trigger_rule import TriggerRule
    from app.models.events_logs.alert_event import AlertEvent
    from app.models.events_logs.firmware_update import FirmwareUpdate
    from app.models.objects.refresh_token import RefreshToken
    from app.models.internal.internal_asset_inventory import InternalAssetInventory
    from app.models.internal.internal_asset_purchase_record import InternalAssetPurchaseRecord
    from app.models.objects.provisioning_token import ProvisioningToken

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

    # 3. 인프라 및 자산 소유
    system_units: Mapped[List["SystemUnit"]] = relationship("SystemUnit", back_populates="user")
    devices: Mapped[List["UserDevice"]] = relationship("UserDevice", back_populates="user")
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
        back_populates="issued_by_user",  # ProvisioningToken 모델 내의 User 참조 필드명 확인 필요
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