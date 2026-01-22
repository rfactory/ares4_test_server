from sqlalchemy import Column, BigInteger, DateTime, UniqueConstraint, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column # Mapped, mapped_column 추가
from typing import Optional # Optional 추가
from datetime import datetime # datetime 임포트 추가
from app.database import Base
from ..base_model import TimestampMixin, UserFKMixin, SubscriptionPlanFKMixin # Mixin 추가

class UserSubscription(Base, TimestampMixin, UserFKMixin, SubscriptionPlanFKMixin): # Mixin 상속
    """
    사용자 구독 모델은 특정 사용자가 어떤 구독 플랜을 사용하고 있는지에 대한 정보를 저장합니다.
    이는 사용자의 서비스 이용 현황을 관리합니다.
    """
    __tablename__ = "user_subscriptions"
    __table_args__ = (
        UniqueConstraint('user_id', 'subscription_plan_id', 'system_unit_id', name='_user_plan_unit_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 사용자 구독의 고유 ID
    # user_id는 UserFKMixin으로부터 상속받습니다. (BigInteger)
    # subscription_plan_id는 SubscriptionPlanFKMixin으로부터 상속받습니다. (BigInteger)
    
    # --- 핵심: 클러스터와 1:1 매칭을 위한 외래키 ---
    # 이 구독권이 어느 클러스터(SystemUnit)에 사용되고 있는지 정의합니다.
    system_unit_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('system_units.id'), nullable=True, unique=True)

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False) # 구독 시작일
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) # 구독 종료일 (Null이면 무제한 또는 현재 진행 중)
    
    # 플랜에서 정한 기본값을 복사해오거나 오버라이드할 수 있는 필드
    max_devices: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 이 사용자가 이 플랜으로 관리할 수 있는 최대 장치 수
    
    # --- Relationships ---
    user = relationship("User", back_populates="subscriptions") # 이 구독에 연결된 사용자 정보
    subscription_plan = relationship("SubscriptionPlan", back_populates="user_subscriptions") # 이 구독에 연결된 구독 플랜 정보
    # 연결된 클러스터와의 관계
    system_unit = relationship("SystemUnit", back_populates="user_subscription")