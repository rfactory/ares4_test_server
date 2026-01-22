from sqlalchemy import Column, BigInteger, DateTime, UniqueConstraint, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from datetime import datetime # datetime 임포트 추가
from app.database import Base
from ..base_model import TimestampMixin, OrganizationFKMixin, SubscriptionPlanFKMixin

class OrganizationSubscription(Base, TimestampMixin, OrganizationFKMixin, SubscriptionPlanFKMixin):
    """
    조직 구독 모델은 특정 조직이 구매한 '구독권(Ticket)'입니다.
    사용자님의 원칙에 따라 이 구독권 하나는 하나의 SystemUnit(클러스터)과 매칭됩니다.
    """
    __tablename__ = "organization_subscriptions"
    __table_args__ = (
        # 하나의 조직이 동일한 플랜을 여러 개 구독할 수 있으므로(클러스터가 여러 개일 때),
        # 상황에 따라 이 유니크 제약은 제거하거나 'system_unit_id'와 묶는 것이 좋습니다.
        UniqueConstraint('organization_id', 'subscription_plan_id', 'system_unit_id', name='_org_plan_unit_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # --- 핵심: 클러스터와 1:1 매칭을 위한 외래키 ---
    # 이 구독권이 어느 클러스터(SystemUnit)에 사용되고 있는지 정의합니다.
    system_unit_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('system_units.id'), nullable=True, unique=True)

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 플랜에서 정한 기본값을 복사해오거나 오버라이드할 수 있는 필드
    max_devices: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_users: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # --- Relationships ---
    organization = relationship("Organization", back_populates="subscriptions")
    subscription_plan = relationship("SubscriptionPlan", back_populates="organization_subscriptions")
    # 연결된 클러스터와의 관계
    system_unit = relationship("SystemUnit", back_populates="subscription")