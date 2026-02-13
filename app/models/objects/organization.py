import enum
from sqlalchemy import BigInteger, String, Boolean, Enum, text, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING, List

from app.database import Base
from ..base_model import TimestampMixin, OrganizationTypeFKMixin

if TYPE_CHECKING:
    # 1. 기초 객체 및 재고
    from app.models.objects.device import Device
    from app.models.relationships.system_unit_assignment import SystemUnitAssignment

    # 2. IAM 및 권한 체계
    from app.models.objects.role import Role
    from app.models.relationships.user_organization_role import UserOrganizationRole
    from app.models.objects.access_request import AccessRequest

    # 3. [공유] 자동화 및 모니터링 (조직 차원의 정책)
    from app.models.relationships.schedule import Schedule
    from app.models.relationships.alert_rule import AlertRule
    from app.models.relationships.trigger_rule import TriggerRule

    # 4. [공유] 운영 로그 및 데이터 (감사 및 컴플라이언스)
    from app.models.events_logs.audit_log import AuditLog
    from app.models.objects.action_log import ActionLog
    from app.models.events_logs.alert_event import AlertEvent
    from app.models.events_logs.consumable_usage_log import ConsumableUsageLog

    # 5. [공유] 유지보수 및 보안 자산
    from app.models.events_logs.firmware_update import FirmwareUpdate
    from app.models.objects.provisioning_token import ProvisioningToken

    # 6. 비즈니스 및 구독
    from app.models.objects.organization_type import OrganizationType
    from app.models.relationships.organization_subscription import OrganizationSubscription

    # 7. [공유] 내부 자산 관리 (Internal Asset Management)
    from app.models.internal.internal_asset_inventory import InternalAssetInventory
    from app.models.internal.internal_asset_purchase_record import InternalAssetPurchaseRecord

class CurrencyType(str, enum.Enum):
    KRW = 'KRW'
    USD = 'USD'

class Organization(Base, TimestampMixin, OrganizationTypeFKMixin):
    """
    [Object] 조직 정보 모델:
    SaaS 시스템의 최상위 운영 주체입니다. 
    개인 사용자(User)와 대칭을 이루는 구조로, 조직 차원의 자산, 정책, 로그를 통합 관리합니다.
    """
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # --- 주요 조직 및 법적 정보 ---
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_registration_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # --- 담당자 및 연락처 ---
    main_contact_person: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # --- 상태 및 로컬 설정 ---
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    
    currency: Mapped[Optional[CurrencyType]] = mapped_column(Enum(CurrencyType), nullable=True)
    
    # --- 비즈니스 확장 데이터 ---
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pg_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # --- Relationships ---

    # 1. 인프라 및 자산 권한 (Inventory & Asset Assignment)
    # [Inventory] 조직 명의로 점유된 하드웨어 목록
    owned_devices: Mapped[List["Device"]] = relationship("Device", back_populates="owner_organization")
    
    # [Asset Assignment] 조직이 OWNER/OPERATOR 권한을 가진 유닛 목록
    system_unit_assignments: Mapped[List["SystemUnitAssignment"]] = relationship(
        "SystemUnitAssignment", back_populates="organization", cascade="all, delete-orphan"
    )
    
    # 2. IAM (보안 및 권한 체계)
    roles: Mapped[List["Role"]] = relationship("Role", back_populates="organization")
    user_roles: Mapped[List["UserOrganizationRole"]] = relationship("UserOrganizationRole", back_populates="organization")
    access_requests: Mapped[List["AccessRequest"]] = relationship("AccessRequest", back_populates="organization")
    
    # 3. 자동화 제어 (조직 공용 정책 - User와 공유)
    schedules: Mapped[List["Schedule"]] = relationship("Schedule", back_populates="organization") # [추가]
    alert_rules: Mapped[List["AlertRule"]] = relationship("AlertRule", back_populates="organization") # [추가]
    trigger_rules: Mapped[List["TriggerRule"]] = relationship("TriggerRule", back_populates="organization") # [추가]
    
    # 4. 운영 로그 및 이력 (Compliance - User와 공유)
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="organization") # [추가]
    action_logs: Mapped[List["ActionLog"]] = relationship("ActionLog", back_populates="organization") # [추가]
    alert_events: Mapped[List["AlertEvent"]] = relationship("AlertEvent", back_populates="organization") # [추가]
    consumable_usage_logs: Mapped[List["ConsumableUsageLog"]] = relationship("ConsumableUsageLog", back_populates="organization") # [추가]
    
    # 5. 시스템 유지보수 (Maintenance - User와 공유)
    firmware_updates: Mapped[List["FirmwareUpdate"]] = relationship("FirmwareUpdate", back_populates="organization") # [추가]
    provisioning_tokens: Mapped[List["ProvisioningToken"]] = relationship("ProvisioningToken", back_populates="organization") # [추가]
    
    # 6. 비즈니스 자산 및 구독
    organization_type: Mapped["OrganizationType"] = relationship("OrganizationType", back_populates="organizations")
    subscriptions: Mapped[List["OrganizationSubscription"]] = relationship("OrganizationSubscription", back_populates="organization")
    
    # 7. 내부 자산 관리 (User 모델의 6번 항목과 대응)
    internal_asset_inventory_updates: Mapped[List["InternalAssetInventory"]] = relationship(
        "InternalAssetInventory", 
        # [수정] last_updated_by_... 가 아니라 실제 컬럼명인 recorded_by_... 로 변경
        foreign_keys="[InternalAssetInventory.recorded_by_organization_id]", 
        back_populates="owner_organization" # InternalAssetInventory의 관계명과 일치
    ) 
    
    internal_asset_purchase_records: Mapped[List["InternalAssetPurchaseRecord"]] = relationship(
        "InternalAssetPurchaseRecord", 
        foreign_keys="[InternalAssetPurchaseRecord.recorded_by_organization_id]", 
        back_populates="recorded_by_organization"
    )

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.company_name})>"