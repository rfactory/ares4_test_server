from sqlalchemy import BigInteger, DateTime, UniqueConstraint, Integer, ForeignKey, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from app.database import Base
from ..base_model import TimestampMixin, OrganizationFKMixin, SubscriptionPlanFKMixin

if TYPE_CHECKING:
    from app.models.objects.organization import Organization
    from app.models.objects.subscription_plan import SubscriptionPlan
    from app.models.objects.system_unit import SystemUnit

class OrganizationSubscription(Base, TimestampMixin, OrganizationFKMixin, SubscriptionPlanFKMixin):
    """
    [Relationship] 조직 구독 모델:
    특정 조직이 구매한 개별 '구독권'입니다. 
    Ares4 원칙에 따라 이 구독권은 하나의 SystemUnit(클러스터)과 1:1로 매핑되어 
    해당 유닛의 운영 권한과 자원 한도를 결정합니다.
    """
    __tablename__ = "organization_subscriptions"
    __table_args__ = (
        # 동일 유닛에 중복 구독권이 발행되는 것을 방지
        UniqueConstraint('organization_id', 'subscription_plan_id', 'system_unit_id', name='_org_plan_unit_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # --- 핵심: 클러스터와 1:1 매칭 (unique=True) ---
    system_unit_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        ForeignKey('system_units.id'), 
        nullable=True, 
        unique=True,
        comment="이 구독권이 할당된 유닛. Null일 경우 아직 미할당된 티켓."
    )

    # 구독 유효 기간
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=text("CURRENT_TIMESTAMP")
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # --- 서비스 가드레일 (Plan 기본값 오버라이드) ---
    # 특정 업체(예: VIP)에게만 기기 수를 더 늘려주는 식의 예외 처리를 지원합니다.
    max_devices: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_users: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # --- Relationships (Mapped 적용 완료) ---
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="subscriptions"
    )
    subscription_plan: Mapped["SubscriptionPlan"] = relationship(
        "SubscriptionPlan", back_populates="organization_subscriptions"
    )
    # 1:1 관계 (SystemUnit 모델에서 uselist=False 설정 필요)
    system_unit: Mapped[Optional["SystemUnit"]] = relationship(
        "SystemUnit", back_populates="subscription"
    )

    def __repr__(self):
        return f"<OrganizationSubscription(id={self.id}, unit={self.system_unit_id}, plan={self.subscription_plan_id})>"