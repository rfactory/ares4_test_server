from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, SubscriptionPlanFKMixin, HardwareBlueprintFKMixin # Mixin 추가

class PlanApplicableBlueprint(Base, TimestampMixin, SubscriptionPlanFKMixin, HardwareBlueprintFKMixin): # Mixin 상속
    """
    플랜 적용 가능 블루프린트 모델은 특정 구독 플랜이 어떤 하드웨어 블루프린트에 적용될 수 있는지 정의합니다.
    이는 구독 플랜과 하드웨어 제품 간의 연결을 설정합니다.
    """
    __tablename__ = "plan_applicable_blueprints"
    __table_args__ = (
        UniqueConstraint('plan_id', 'hardware_blueprint_id', name='_plan_blueprint_uc'), # Changed blueprint_id to hardware_blueprint_id
    )

    id = Column(Integer, primary_key=True, index=True) # 플랜 적용 가능 블루프린트 관계의 고유 ID
    # plan_id는 SubscriptionPlanFKMixin으로부터 상속받습니다.
    # hardware_blueprint_id는 HardwareBlueprintFKMixin으로부터 상속받습니다.
    
    # --- Relationships ---
    subscription_plan = relationship("SubscriptionPlan", back_populates="plan_applicable_blueprints") # 이 관계에 연결된 구독 플랜 정보
    hardware_blueprint = relationship("HardwareBlueprint", back_populates="plan_applicable_blueprints") # 이 관계에 연결된 하드웨어 블루프린트 정보