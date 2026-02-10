from sqlalchemy import BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, SubscriptionPlanFKMixin

if TYPE_CHECKING:
    from app.models.objects.subscription_plan import SubscriptionPlan

class SubscriptionPlanFeature(Base, TimestampMixin, SubscriptionPlanFKMixin):
    """
    [Object] 구독 플랜 기능 모델:
    특정 구독 플랜이 허용하는 구체적인 기능 플래그와 제약 수치를 관리합니다.
    마스터플랜 3에서 제3자 MSA 블록의 접근 권한을 제어하는 핵심 기준이 됩니다.
    """
    __tablename__ = "subscription_plan_features"
    __table_args__ = (
        # 하나의 플랜 내에서 동일한 기능 키가 중복 정의되는 것을 방지
        UniqueConstraint('subscription_plan_id', 'feature_key', name='_plan_feature_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 기능의 고유 키 (예: 'ENABLE_AI_VISION', 'DATA_RETENTION_DAYS', 'MAX_MSA_BLOCKS')
    feature_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True) 
    
    # 기능의 구체적 값 (예: 'true', '90', '5') 
    # 애플리케이션 레벨에서 key에 따라 형변환하여 사용합니다.
    feature_value: Mapped[str] = mapped_column(Text, nullable=False) 
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) 

    # --- Relationships (Mapped 적용 완료) ---
    subscription_plan: Mapped["SubscriptionPlan"] = relationship(
        "SubscriptionPlan", 
        back_populates="features"
    )

    def __repr__(self):
        return f"<SubscriptionPlanFeature(key={self.feature_key}, value={self.feature_value})>"