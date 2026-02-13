from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Float, Text, Integer, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from app.database import Base
from ..base_model import TimestampMixin, AssetDefinitionFKMixin

if TYPE_CHECKING:
    from .internal_asset_definition import InternalAssetDefinition
    from ..objects.user import User
    from ..objects.organization import Organization

class InternalAssetPurchaseRecord(Base, TimestampMixin, AssetDefinitionFKMixin):
    """
    [Finance/Inventory] 내부 자산 구매 기록 모델:
    자산의 도입 시점, 가격, 공급처 정보를 기록하여 자산 가치 및 이력을 관리합니다.
    """
    __tablename__ = "internal_asset_purchase_records"
    __table_args__ = (
        CheckConstraint(
            "(recorded_by_organization_id IS NOT NULL AND recorded_by_user_id IS NULL) OR "
            "(recorded_by_organization_id IS NULL AND recorded_by_user_id IS NOT NULL)",
            name="check_exclusive_purchase_record_owner"
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    recorded_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True, index=True)
    recorded_by_organization_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('organizations.id'), nullable=True, index=True)
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="구매 수량")
    purchase_price_per_unit: Mapped[float] = mapped_column(Float, nullable=False, comment="단가")
    
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="공급업체 명")
    purchase_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    invoice_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="송장 번호")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 기록한 담당자 정보
    recorded_by_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey('users.id'), nullable=True
    )

    # --- Relationships (Mapped 적용 완료) ---
    
    # 구매한 자산의 정의 (청사진) 정보
    asset_definition: Mapped["InternalAssetDefinition"] = relationship("InternalAssetDefinition", back_populates="purchase_records")
    
    # 이 기록을 생성한 담당자 (User 모델의 back_populates와 매칭)
    recorded_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[recorded_by_user_id], back_populates="internal_asset_purchase_records")
    recorded_by_organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", 
        foreign_keys=[recorded_by_organization_id], # 명시적 지정
        back_populates="internal_asset_purchase_records"
    )