import enum
from sqlalchemy import BigInteger, Integer, Text, String, Boolean, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from app.database import Base
from ..base_model import TimestampMixin, AssetDefinitionFKMixin, SystemUnitFKMixin

if TYPE_CHECKING:
    from ..objects.system_unit import SystemUnit
    from .internal_asset_definition import InternalAssetDefinition

# 교체 사유나 출처를 명확히 관리
class ComponentSourceType(str, enum.Enum):
    INITIAL = "INITIAL"           # 초기 조립
    WARRANTY = "WARRANTY"         # 무상 보증 수리
    PAID_REPAIR = "PAID_REPAIR"   # 유상 수리
    DIY_REPLACEMENT = "DIY_REPLACEMENT" # 사용자 직접 교체

class InternalSystemUnitPhysicalComponent(Base, TimestampMixin, SystemUnitFKMixin, AssetDefinitionFKMixin):
    """
    [Inventory/Real-world] 내부 시스템 유닛 물리 컴포넌트 모델:
    특정 기기(SystemUnit)에 실제로 장착된 개별 부품(껍데기, 센서, PCB 등)의 생애주기를 관리합니다.
    """
    __tablename__ = "internal_system_unit_physical_components"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 장착 위치 태그 (예: 'SENS_L1', 'CASE_UPPER', 'MOTOR_M1')
    position_tag: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # 현재 작동/장착 여부
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # 부품의 출처/교체 유형
    source_type: Mapped[ComponentSourceType] = mapped_column(
        Enum(ComponentSourceType, name="component_source_type", create_type=False), 
        default=ComponentSourceType.INITIAL, 
        nullable=False
    )
    
    change_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    assembly_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 시간 관리: func.now()를 사용하여 DB 서버 시간 기준으로 기록 권장
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Relationships (Mapped 적용 완료) ---
    
    # 부모: 이 부품이 장착된 실물 기기 유닛
    system_unit: Mapped["SystemUnit"] = relationship(
        "SystemUnit", 
        back_populates="physical_components"
    )
    
    # 참조: 이 부품의 사양 정보 (Master Data)
    asset_definition: Mapped["InternalAssetDefinition"] = relationship(
        "InternalAssetDefinition",
        back_populates="physical_components"
    )