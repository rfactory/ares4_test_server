from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, UserFKMixin, SubscriptionPlanFKMixin # Mixin 추가

class UserSubscription(Base, TimestampMixin, UserFKMixin, SubscriptionPlanFKMixin): # Mixin 상속
    """
    사용자 구독 모델은 특정 사용자가 어떤 구독 플랜을 사용하고 있는지에 대한 정보를 저장합니다.
    이는 사용자의 서비스 이용 현황을 관리합니다.
    """
    __tablename__ = "user_subscriptions"
    __table_args__ = (
        UniqueConstraint('user_id', 'plan_id', name='_user_plan_uc'), # plan_id로 변경
    )

    id = Column(Integer, primary_key=True, index=True) # 사용자 구독의 고유 ID
    # user_id는 UserFKMixin으로부터 상속받습니다.
    # plan_id는 SubscriptionPlanFKMixin으로부터 상속받습니다.
    start_date = Column(DateTime(timezone=True), nullable=False) # 구독 시작일
    end_date = Column(DateTime(timezone=True), nullable=True) # 구독 종료일 (Null이면 무제한 또는 현재 진행 중)
    
    # --- Relationships ---
    user = relationship("User", back_populates="subscriptions") # 이 구독에 연결된 사용자 정보
    subscription_plan = relationship("SubscriptionPlan", back_populates="user_subscriptions") # 이 구독에 연결된 구독 플랜 정보