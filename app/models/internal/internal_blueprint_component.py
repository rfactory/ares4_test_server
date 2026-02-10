from sqlalchemy import BigInteger, UniqueConstraint, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING

from app.database import Base
from ..base_model import TimestampMixin, HardwareBlueprintFKMixin, AssetDefinitionFKMixin

if TYPE_CHECKING:
    # 순환 참조 방지 및 타입 힌트 제공
    from ..objects.hardware_blueprint import HardwareBlueprint
    from .internal_asset_definition import InternalAssetDefinition

class InternalBlueprintComponent(Base, TimestampMixin, HardwareBlueprintFKMixin, AssetDefinitionFKMixin):
    """
    [Master/BOM] 내부 블루프린트 컴포넌트 모델:
    특정 하드웨어 설계도(HardwareBlueprint)를 구성하는 표준 자재 명세서(Standard BOM) 정보를 관리합니다.
    """
    __tablename__ = "internal_blueprint_components"
    __table_args__ = (
        # 동일한 설계도 내에 동일한 부품이 중복 정의되는 것을 방지
        UniqueConstraint('hardware_blueprint_id', 'asset_definition_id', name='_blueprint_asset_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) 
    
    # 해당 설계도 구현을 위해 필요한 부품의 수량
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1) 
    
    # --- Relationships (Mapped 적용 완료) ---
    
    # 부모: 이 컴포넌트 구성을 포함하는 상위 설계도
    blueprint: Mapped["HardwareBlueprint"] = relationship(
        "HardwareBlueprint", 
        back_populates="internal_blueprint_components"
    ) 
    
    # 참조: 이 항목이 가리키는 구체적인 부품 정의(Master Data)
    asset_definition: Mapped["InternalAssetDefinition"] = relationship(
        "InternalAssetDefinition", 
        back_populates="blueprint_components"
    )

    def __repr__(self):
        return f"<InternalBlueprintComponent(blueprint_id={self.hardware_blueprint_id}, asset_id={self.asset_definition_id}, qty={self.quantity})>"