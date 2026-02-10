import enum
from sqlalchemy import BigInteger, String, DateTime, Text, Integer, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from app.database import Base
from ..base_model import TimestampMixin, UserFKMixin, AssetDefinitionFKMixin

if TYPE_CHECKING:
    from app.models.objects.user import User
    from app.models.internal.internal_asset_definition import InternalAssetDefinition
    from app.models.events_logs.consumable_usage_log import ConsumableUsageLog

# 1. 소모품 상태 관리를 위한 Enum 정의
class ConsumableStatus(str, enum.Enum):
    ACTIVE = 'ACTIVE'       # 사용 가능
    USED_UP = 'USED_UP'     # 소진됨
    EXPIRED = 'EXPIRED'     # 만료됨
    DISCARDED = 'DISCARDED' # 폐기됨

class UserConsumable(Base, TimestampMixin, UserFKMixin, AssetDefinitionFKMixin):
    """
    사용자 소모품 모델: 특정 사용자가 소유한 소모품의 인스턴스를 관리합니다.
    """
    __tablename__ = "user_consumables"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    purchase_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    current_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # 2. String 대신 Enum 적용으로 데이터 무결성 강화
    status: Mapped[ConsumableStatus] = mapped_column(
        Enum(ConsumableStatus, name='consumable_instance_status', create_type=False), 
        default=ConsumableStatus.ACTIVE, 
        nullable=False
    )
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # --- Relationships (Mapped 적용 완료) ---

    user: Mapped["User"] = relationship(
        "User", back_populates="user_consumables"
    )
    
    asset_definition: Mapped["InternalAssetDefinition"] = relationship(
        "InternalAssetDefinition", back_populates="user_consumables"
    )
    
    # 이 소모품의 사용 로그 (ConsumableUsageLog의 user_consumable 관계와 짝꿍)
    usage_logs: Mapped[List["ConsumableUsageLog"]] = relationship(
        "ConsumableUsageLog", back_populates="user_consumable", cascade="all, delete-orphan"
    )