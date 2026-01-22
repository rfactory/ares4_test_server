# app/models/internal/internal_asset_inventory.py
from sqlalchemy import Column, BigInteger, String, ForeignKey, UniqueConstraint, Integer # Integer (quantity)
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional # Added Optional

from app.database import Base
from ..base_model import TimestampMixin, AssetDefinitionFKMixin # NullableUserFKMixin 제거
class InternalAssetInventory(Base, TimestampMixin, AssetDefinitionFKMixin): # Mixin 상속 제거
    """
    내부 자산 재고 모델은 회사에서 관리하는 자산의 현재 재고 수량과 위치를 추적합니다.
    """
    __tablename__ = "internal_asset_inventory"
    __table_args__ = (
        UniqueConstraint('asset_definition_id', 'location', name='_asset_location_uc'),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 재고 항목의 고유 ID
    # asset_definition_id는 AssetDefinitionFKMixin으로부터 상속받습니다. (BigInteger)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False) # 현재 재고 수량
    location: Mapped[str] = mapped_column(String(100), nullable=False) # 자산이 보관된 물리적 위치 (예: '창고 A', '생산 라인 1')
   
    # 명시적으로 외래 키 컬럼 정의
    last_updated_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True) # 재고 변경을 마지막으로 수행한 사용자 ID
   
    # --- Relationships ---
    asset_definition = relationship("InternalAssetDefinition", back_populates="inventory_items") # 이 재고 항목이 정의하는 자산 정보
    last_updated_by_user = relationship("User", foreign_keys=[last_updated_by_user_id]) # 재고 변경을 마지막으로 수행한 사용자 정보