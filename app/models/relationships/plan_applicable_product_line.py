from sqlalchemy import BigInteger, Integer, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, SubscriptionPlanFKMixin, ProductLineFKMixin

# 1. 정적 분석 도구를 위한 타입 임포트 (런타임 순환 참조 방지)
if TYPE_CHECKING:
    from app.models.objects.subscription_plan import SubscriptionPlan
    from app.models.objects.product_line import ProductLine

class PlanApplicableProductLine(Base, TimestampMixin, SubscriptionPlanFKMixin, ProductLineFKMixin):
    """
    [Relationship] 플랜별 제품군 메뉴판:
    특정 구독 플랜이 어떤 제품군(ProductLine)을 몇 개까지 지원하는지 정의합니다.
    """
    __tablename__ = "plan_applicable_product_lines"
    __table_args__ = (
        # 동일 플랜에 동일 제품군이 중복 등록되는 것을 방지
        UniqueConstraint('subscription_plan_id', 'product_line_id', name='_plan_product_line_uc'),
    )

    # 2. Mapped[int]를 통한 명확한 타입 정의 (Any 제거)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 해당 플랜 사용자가 이 제품군(클러스터 유형)을 최대 몇 개까지 보유할 수 있는지 수치
    max_unit_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # 3. 관계(Relationship)에 대한 엄격한 타입 어노테이션
    subscription_plan: Mapped["SubscriptionPlan"] = relationship(
        "SubscriptionPlan", 
        back_populates="plan_applicable_product_lines"
    )
    product_line: Mapped["ProductLine"] = relationship(
        "ProductLine", 
        back_populates="plan_applicable_product_lines"
    )

    def __repr__(self) -> str:
        return f"<PlanApplicableProductLine(plan={self.subscription_plan_id}, product_line={self.product_line_id})>"