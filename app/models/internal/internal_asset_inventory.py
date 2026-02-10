from sqlalchemy import BigInteger, String, ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING

from app.database import Base
from ..base_model import TimestampMixin, AssetDefinitionFKMixin

if TYPE_CHECKING:
    from .internal_asset_definition import InternalAssetDefinition
    from ..objects.user import User

class InternalAssetInventory(Base, TimestampMixin, AssetDefinitionFKMixin):
    """
    [Inventory] 내부 자산 재고 모델:
    특정 부품(AssetDefinition)이 위치별로 몇 개 남아있는지 실제 수량을 관리합니다.
    """
    __tablename__ = "internal_asset_inventory"
    __table_args__ = (
        UniqueConstraint('asset_definition_id', 'location', name='_asset_location_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 실재고 수량
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # 보관 위치 (예: 'Main_Warehouse_A', 'Lab_Desk_1')
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 마지막으로 수량을 수정한 사용자
    last_updated_by_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey('users.id'), nullable=True
    )
    
    # --- Relationships (Mapped 적용 완료) ---
    
    # 청사진 정보 (1:N 관계의 N쪽)
    asset_definition: Mapped["InternalAssetDefinition"] = relationship(
        "InternalAssetDefinition", back_populates="inventory_items"
    )
    
    # 수정자 정보 (User 모델의 back_populates 명칭과 일치시킴)
    last_updated_by_user: Mapped[Optional["User"]] = relationship(
        "User", 
        foreign_keys=[last_updated_by_user_id],
        back_populates="internal_asset_inventory_updates" 
    )