from sqlalchemy import BigInteger, String, ForeignKey, UniqueConstraint, Integer, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, AssetDefinitionFKMixin

if TYPE_CHECKING:
    from .internal_asset_definition import InternalAssetDefinition
    from ..objects.user import User
    from ..objects.organization import Organization

class InternalAssetInventory(Base, TimestampMixin, AssetDefinitionFKMixin):
    """
    [Inventory] 내부 자산 재고 모델:
    특정 부품(AssetDefinition)이 위치별로 몇 개 남아있는지 실제 수량을 관리합니다.
    """
    __tablename__ = "internal_asset_inventory"
    __table_args__ = (
        # 특정 조직/개인의 특정 위치에는 하나의 부품 정의만 존재해야 함
        UniqueConstraint('asset_definition_id', 'location', 'owner_organization_id', 'owner_user_id', name='_asset_owner_location_uc'),
        # [XOR 제약] 소유자는 유저 혹은 조직 중 하나여야 함
        CheckConstraint(
            "(owner_user_id IS NOT NULL AND owner_organization_id IS NULL) OR "
            "(owner_user_id IS NULL AND owner_organization_id IS NOT NULL)",
            name="check_exclusive_asset_inventory_owner"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 소유권
    recorded_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True, index=True)
    recorded_by_organization_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('organizations.id'), nullable=True, index=True)
    
    # 실재고 수량
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # 보관 위치 (예: 'Main_Warehouse_A', 'Lab_Desk_1')
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 마지막으로 수량을 수정한 사용자
    last_updated_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)
    
    # --- Relationships (Mapped 적용 완료) ---
    
    # 청사진 정보 (1:N 관계의 N쪽)
    asset_definition: Mapped["InternalAssetDefinition"] = relationship("InternalAssetDefinition", back_populates="inventory_items")
    
    # 수정자 정보 (User 모델의 back_populates 명칭과 일치시킴)
    last_updated_by_user: Mapped[Optional["User"]] = relationship(
        "User", 
        foreign_keys=[last_updated_by_user_id],
        back_populates="internal_asset_inventory_updates" 
    )
    owner_organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="internal_asset_inventory_updates")