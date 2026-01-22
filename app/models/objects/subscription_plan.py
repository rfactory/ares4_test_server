from sqlalchemy import Column, BigInteger, String, Text, Boolean, Float, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    from app.models.relationships.plan_applicable_product_line import PlanApplicableProductLine
    from app.models.relationships.user_subscription import UserSubscription
    from app.models.relationships.organization_subscription import OrganizationSubscription
    from app.models.relationships.subscription_plan_feature import SubscriptionPlanFeature

class SubscriptionPlan(Base, TimestampMixin):
    """
    구독 플랜 모델은 사용자 또는 조직이 선택할 수 있는 다양한 서비스 구독 옵션을 정의합니다.
    각 플랜은 가격, 기간, 제공되는 기능 등을 포함합니다.
    """
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 구독 플랜의 고유 ID
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False) # 구독 플랜의 이름 (예: 'Basic', 'Premium')
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 구독 플랜에 대한 상세 설명

    # --- 가격 및 기간 ---
    price_monthly: Mapped[float] = mapped_column(Float, nullable=False) # 월별 구독 가격
    price_yearly: Mapped[float] = mapped_column(Float, nullable=False) # 연간 구독 가격
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 구독 기간 (일 단위). Null이면 무제한.
    trial_period_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 무료 체험 기간 (일 단위)
    # --- 기타 ---
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # 구독 플랜의 활성화 여부
    
    # --- Relationships ---
    # 개별 하드웨어가 아닌, 라즈베리파이 클러스터 설계도(ProductLine)와 직접 연결되도록 수정되었습니다.
    plan_applicable_product_lines: Mapped[List["PlanApplicableProductLine"]] = relationship("PlanApplicableProductLine", back_populates="subscription_plan") # 이 플랜이 적용 가능한 제품 라인(클러스터 설계도) 목록
    user_subscriptions: Mapped[List["UserSubscription"]] = relationship("UserSubscription", back_populates="subscription_plan") # 이 플랜을 구독하는 사용자 구독 정보 목록
    organization_subscriptions: Mapped[List["OrganizationSubscription"]] = relationship("OrganizationSubscription", back_populates="subscription_plan") # 이 플랜을 구독하는 조직 구독 정보 목록
    features: Mapped[List["SubscriptionPlanFeature"]] = relationship("SubscriptionPlanFeature", back_populates="subscription_plan") # 이 구독 플랜에 포함된 기능 목록