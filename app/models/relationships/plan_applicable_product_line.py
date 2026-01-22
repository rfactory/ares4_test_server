# app/models/relationships/plan_applicable_product_line.py
from sqlalchemy import BigInteger, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column # Mapped, mapped_column 추가
from app.database import Base
from ..base_model import TimestampMixin

class PlanApplicableProductLine(Base, TimestampMixin):
    """
    특정 구독 플랜으로 어떤 제품군(클러스터 설계도)을 
    어느 정도 규모로 사용할 수 있는지 정의하는 '메뉴판' 테이블입니다.
    """
    __tablename__ = "plan_applicable_product_lines"
    __table_args__ = (
        UniqueConstraint('subscription_plan_id', 'product_line_id', name='_plan_product_line_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    subscription_plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subscription_plans.id"), nullable=False)
    product_line_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("product_lines.id"), nullable=False)
    
    # 해당 플랜 사용자가 이 클러스터 유형을 최대 몇 개까지 보유할 수 있는지
    max_unit_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # --- Relationships ---
    subscription_plan = relationship("SubscriptionPlan", back_populates="plan_applicable_product_lines")
    product_line = relationship("ProductLine", back_populates="plan_applicable_product_lines")
