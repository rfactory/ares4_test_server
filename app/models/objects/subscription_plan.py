from sqlalchemy import BigInteger, String, Text, Boolean, Numeric, Integer
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
    [Object] 구독 플랜 모델:
    사용자 또는 조직이 선택할 수 있는 서비스 옵션과 가격 정책을 정의합니다.
    제품 라인(ProductLine) 기반으로 권한이 해제되는 구조를 가집니다.
    """
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 플랜 명칭 (예: 'Lite', 'Pro', 'Enterprise')
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- 가격 정책 (정밀한 계산을 위해 Numeric 권장) ---
    # precision=10, scale=2: 총 10자리, 소수점 2자리까지 지원
    price_monthly: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_yearly: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    
    # --- 기간 설정 ---
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Null이면 평생/무제한
    trial_period_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 무료 체험 기간
    
    # 플랜 판매 상태
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # --- Relationships (Mapped 적용 완료) ---
    
    # 1. 제품군 권한: 이 요금제 가입 시 사용할 수 있는 장치 설계도(ProductLine) 목록
    plan_applicable_product_lines: Mapped[List["PlanApplicableProductLine"]] = relationship(
        "PlanApplicableProductLine", back_populates="subscription_plan", cascade="all, delete-orphan"
    )
    
    # 2. 기능 상세: 이 요금제에 포함된 구체적인 기능 플래그 (예: 'AI_ANALYTICS: True')
    features: Mapped[List["SubscriptionPlanFeature"]] = relationship(
        "SubscriptionPlanFeature", back_populates="subscription_plan", cascade="all, delete-orphan"
    )
    
    # 3. 구독 인스턴스: 이 플랜을 실제로 구독 중인 유저/조직 정보
    user_subscriptions: Mapped[List["UserSubscription"]] = relationship(
        "UserSubscription", back_populates="subscription_plan"
    )
    organization_subscriptions: Mapped[List["OrganizationSubscription"]] = relationship(
        "OrganizationSubscription", back_populates="subscription_plan"
    )

    def __repr__(self):
        return f"<SubscriptionPlan(name={self.name}, price={self.price_monthly})>"