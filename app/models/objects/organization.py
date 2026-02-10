import enum
from sqlalchemy import BigInteger, String, Boolean, Enum, text, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING, List

from app.database import Base
from ..base_model import TimestampMixin, OrganizationTypeFKMixin

if TYPE_CHECKING:
    from app.models.objects.organization_type import OrganizationType
    from app.models.objects.system_unit import SystemUnit
    from app.models.objects.role import Role
    from app.models.relationships.user_organization_role import UserOrganizationRole
    from app.models.relationships.organization_device import OrganizationDevice
    from app.models.relationships.organization_subscription import OrganizationSubscription
    from app.models.objects.access_request import AccessRequest

class CurrencyType(str, enum.Enum):
    KRW = 'KRW'
    USD = 'USD'

class Organization(Base, TimestampMixin, OrganizationTypeFKMixin):
    """
    [Object] 조직 정보 모델:
    SaaS 시스템의 최상위 단위이며, 모든 자산(SystemUnit, Device)의 법적 소유주입니다.
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
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # 예: 'Asia/Seoul'
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    
    currency: Mapped[Optional[CurrencyType]] = mapped_column(
        Enum(CurrencyType, name='currency_type', create_type=False), 
        nullable=True
    )
    
    # --- 비즈니스 확장 데이터 ---
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pg_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # --- Relationships ---

    # 1. 운영 핵심 자산 (SystemUnit 계층)
    system_units: Mapped[List["SystemUnit"]] = relationship(
        "SystemUnit", back_populates="organization", cascade="all, delete-orphan"
    )
    
    # 2. 보안 및 권한 체계
    roles: Mapped[List["Role"]] = relationship(
        "Role", back_populates="organization"
    ) 
    user_roles: Mapped[List["UserOrganizationRole"]] = relationship(
        "UserOrganizationRole", back_populates="organization"
    )
    access_requests: Mapped[List["AccessRequest"]] = relationship(
        "AccessRequest", back_populates="organization"
    )
    
    # 3. 인프라 매핑
    organization_devices: Mapped[List["OrganizationDevice"]] = relationship(
        "OrganizationDevice", back_populates="organization"
    )
    organization_type: Mapped["OrganizationType"] = relationship(
        "OrganizationType", back_populates="organizations"
    )
    
    # 4. 결제/구독 비즈니스
    subscriptions: Mapped[List["OrganizationSubscription"]] = relationship(
        "OrganizationSubscription", back_populates="organization"
    )

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.company_name})>"