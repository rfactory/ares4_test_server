from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, ProductLineFKMixin

if TYPE_CHECKING:
    from .product_line import ProductLine
    from .device import Device
    from ..relationships.blueprint_valid_pin import BlueprintValidPin
    from ..internal.internal_blueprint_component import InternalBlueprintComponent
    from ..relationships.blueprint_pin_mapping import BlueprintPinMapping
    from ..events_logs.firmware_update import FirmwareUpdate

class HardwareBlueprint(Base, TimestampMixin, ProductLineFKMixin):
    """
    [Object] 하드웨어 블루프린트 모델:
    특정 기기 유형의 물리적 구성을 정의하며, 하드웨어의 표준 명세서(DNA) 역할을 합니다.
    """
    __tablename__ = "hardware_blueprints"
    __table_args__ = (
        UniqueConstraint('blueprint_version', 'blueprint_name', name='_blueprint_version_name_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    blueprint_version: Mapped[str] = mapped_column(String(50), nullable=False)
    blueprint_name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    specs: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=True, default={})

    # --- Relationships (Mapped 적용 완료) ---

    # 1. 인프라 계층
    product_line: Mapped["ProductLine"] = relationship(
        "ProductLine", back_populates="hardware_blueprints"
    )
    
    devices: Mapped[List["Device"]] = relationship(
        "Device", back_populates="hardware_blueprint"
    )
    
    # 2. 물리적 사양/핀 맵 계층 (에지 기기 제어의 핵심)
    blueprint_valid_pins: Mapped[List["BlueprintValidPin"]] = relationship(
        "BlueprintValidPin", back_populates="blueprint", cascade="all, delete-orphan"
    )
    
    blueprint_pin_mappings: Mapped[List["BlueprintPinMapping"]] = relationship(
        "BlueprintPinMapping", back_populates="blueprint", cascade="all, delete-orphan"
    )
    
    # 3. 자재 명세서(Standard BOM) 계층
    internal_blueprint_components: Mapped[List["InternalBlueprintComponent"]] = relationship(
        "InternalBlueprintComponent", back_populates="blueprint", cascade="all, delete-orphan"
    )
    
    # 4. 소프트웨어/펌웨어 관리 계층
    firmware_updates: Mapped[List["FirmwareUpdate"]] = relationship(
        "FirmwareUpdate", back_populates="hardware_blueprint"
    )

    def __repr__(self):
        return f"<HardwareBlueprint(name={self.blueprint_name}, version={self.blueprint_version})>"