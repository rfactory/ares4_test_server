from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, OrganizationFKMixin, SubscriptionPlanFKMixin # Mixin 추가

class OrganizationSubscription(Base, TimestampMixin, OrganizationFKMixin, SubscriptionPlanFKMixin): # Mixin 상속
    """
    조직 구독 모델은 특정 조직이 어떤 구독 플랜을 사용하고 있는지에 대한 정보를 저장합니다.
    이는 조직의 서비스 이용 현황 및 제한 사항을 관리합니다.
    """
    __tablename__ = "organization_subscriptions"
    __table_args__ = (
        UniqueConstraint('organization_id', 'plan_id', name='_org_plan_uc'), # plan_id로 변경
    )

    id = Column(Integer, primary_key=True, index=True) # 조직 구독의 고유 ID
    # organization_id는 OrganizationFKMixin으로부터 상속받습니다.
    # plan_id는 SubscriptionPlanFKMixin으로부터 상속받습니다.
    start_date = Column(DateTime(timezone=True), nullable=False) # 구독 시작일
    end_date = Column(DateTime(timezone=True), nullable=True) # 구독 종료일 (Null이면 무제한 또는 현재 진행 중)
    max_devices = Column(Integer, nullable=True) # 이 조직이 이 플랜으로 관리할 수 있는 최대 장치 수
    max_users = Column(Integer, nullable=True) # 이 조직이 이 플랜으로 가질 수 있는 최대 사용자 수
    
    # --- Relationships ---
    organization = relationship("Organization", back_populates="subscriptions") # 이 구독에 연결된 조직 정보
    subscription_plan = relationship("SubscriptionPlan", back_populates="organization_subscriptions") # 이 구독에 연결된 구독 플랜 정보