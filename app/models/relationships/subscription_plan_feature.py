from sqlalchemy import Column, BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column # Mapped, mapped_column 추가
from typing import Optional # Optional 추가 (JSON 때문에 필요할 수 있음)
from app.database import Base
from ..base_model import TimestampMixin, SubscriptionPlanFKMixin # Mixin 추가

class SubscriptionPlanFeature(Base, TimestampMixin, SubscriptionPlanFKMixin):
    """
    구독 플랜 기능 모델은 특정 구독 플랜에 포함된 개별 기능을 정의합니다.
    이는 SubscriptionPlan 모델의 'features' JSON 컬럼을 구조화하여 관계형 데이터베이스의 이점을 활용합니다.
    """
    __tablename__ = "subscription_plan_features"
    __table_args__ = (
        UniqueConstraint('subscription_plan_id', 'feature_key', name='_plan_feature_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 구독 플랜 기능의 고유 ID
    # subscription_plan_id는 SubscriptionPlanFKMixin으로부터 상속받습니다. (BigInteger)
    feature_key: Mapped[str] = mapped_column(String(100), nullable=False) # 기능의 키 (예: 'max_devices', 'cloud_storage_gb')
    feature_value: Mapped[str] = mapped_column(Text, nullable=False) # 기능의 값 (예: '10', '50')
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 기능에 대한 설명
    # --- Relationships ---
    subscription_plan = relationship("SubscriptionPlan", back_populates="features") # 이 기능이 속한 구독 플랜 정보