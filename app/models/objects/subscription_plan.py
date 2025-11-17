from sqlalchemy import Column, Integer, String, Text, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin

class SubscriptionPlan(Base, TimestampMixin):
    """
    구독 플랜 모델은 사용자 또는 조직이 선택할 수 있는 다양한 서비스 구독 옵션을 정의합니다.
    각 플랜은 가격, 기간, 제공되는 기능 등을 포함합니다.
    """
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True) # 구독 플랜의 고유 ID
    name = Column(String(100), unique=True, nullable=False) # 구독 플랜의 이름 (예: 'Basic', 'Premium')
    description = Column(Text, nullable=True) # 구독 플랜에 대한 상세 설명
    
    # --- 가격 및 기간 ---
    price_monthly = Column(Float, nullable=False) # 월별 구독 가격
    price_yearly = Column(Float, nullable=False) # 연간 구독 가격
    duration_days = Column(Integer, nullable=True) # 구독 기간 (일 단위). Null이면 무제한.
    
    # --- 기타 ---
    is_active = Column(Boolean, default=True, nullable=False) # 구독 플랜의 활성화 여부
    
    # --- Relationships ---
    plan_applicable_blueprints = relationship("PlanApplicableBlueprint", back_populates="subscription_plan") # 이 플랜이 적용 가능한 하드웨어 블루프린트 목록
    user_subscriptions = relationship("UserSubscription", back_populates="subscription_plan") # 이 플랜을 구독하는 사용자 구독 정보 목록
    organization_subscriptions = relationship("OrganizationSubscription", back_populates="subscription_plan") # 이 플랜을 구독하는 조직 구독 정보 목록
    features = relationship("SubscriptionPlanFeature", back_populates="subscription_plan") # 이 구독 플랜에 포함된 기능 목록