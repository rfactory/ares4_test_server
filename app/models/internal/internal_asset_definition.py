import enum
from sqlalchemy import BigInteger, String, Text, JSON, Enum, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING

from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    from .internal_asset_inventory import InternalAssetInventory
    from .internal_asset_purchase_record import InternalAssetPurchaseRecord
    from .internal_blueprint_component import InternalBlueprintComponent
    from .internal_system_unit_physical_component import InternalSystemUnitPhysicalComponent
    from ..events_logs.user_consumable import UserConsumable
    from ..objects.supported_component import SupportedComponent

# 1. 관리 편의성을 위한 Enum 클래스 정의
class AssetClass(str, enum.Enum):
    HARDWARE_COMPONENT = 'HARDWARE_COMPONENT'
    PERISHABLE_GOOD = 'PERISHABLE_GOOD'
    STRUCTURAL_COMPONENT = 'STRUCTURAL_COMPONENT'

class PinConnectionType(str, enum.Enum):
    GPIO = 'GPIO'
    I2C = 'I2C'
    SPI = 'SPI'
    UART = 'UART'
    ANALOG = 'ANALOG'

class InternalAssetDefinition(Base, TimestampMixin):
    """
    [Master] 내부 자산 정의 모델: 모든 부품, 소모품, 구조물의 청사진 데이터를 관리합니다.
    """
    __tablename__ = "internal_asset_definitions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) 
    
    # 2. Enum 적용 (Ares4 표준)
    asset_class: Mapped[AssetClass] = mapped_column(
        Enum(AssetClass, name='asset_class', create_type=False), 
        nullable=False
    ) 
    
    supported_component_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("supported_components.id"), nullable=True
    )
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    manufacturer: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) 
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) 

    pin_connection_type: Mapped[Optional[PinConnectionType]] = mapped_column(
        Enum(PinConnectionType, name='pin_connection_type', create_type=False), 
        nullable=True
    )
    
    default_pin_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_lifespan_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    typical_shelf_life_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # --- Relationships (Mapped 스타일 통일 완료) ---
    supported_component: Mapped["SupportedComponent"] = relationship("SupportedComponent")
    
    inventory_items: Mapped[List["InternalAssetInventory"]] = relationship(
        "InternalAssetInventory", back_populates="asset_definition"
    )
    purchase_records: Mapped[List["InternalAssetPurchaseRecord"]] = relationship(
        "InternalAssetPurchaseRecord", back_populates="asset_definition"
    )
    blueprint_components: Mapped[List["InternalBlueprintComponent"]] = relationship(
        "InternalBlueprintComponent", back_populates="asset_definition"
    )
    user_consumables: Mapped[List["UserConsumable"]] = relationship(
        "UserConsumable", back_populates="asset_definition"
    )
    physical_components: Mapped[List["InternalSystemUnitPhysicalComponent"]] = relationship(
        "InternalSystemUnitPhysicalComponent", back_populates="asset_definition"
    )