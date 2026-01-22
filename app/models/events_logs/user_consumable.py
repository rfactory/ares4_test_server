from sqlalchemy import Column, BigInteger, String, DateTime, Text, Integer # Integer (quantity, current_quantity)
from sqlalchemy.orm import relationship, Mapped, mapped_column # Mapped, mapped_column 추가
from typing import Optional, List, TYPE_CHECKING # Optional, TYPE_CHECKING 추가
from datetime import datetime # datetime 추가
from app.database import Base
from ..base_model import TimestampMixin, UserFKMixin, AssetDefinitionFKMixin # Mixin 추가

# 런타임 순환 참조 방지 및 타입 힌트 지원
if TYPE_CHECKING:
    from app.models.objects.user import User
    from app.models.internal.internal_asset_definition import InternalAssetDefinition
    from app.models.events_logs.consumable_usage_log import ConsumableUsageLog

class UserConsumable(Base, TimestampMixin, UserFKMixin, AssetDefinitionFKMixin): # Mixin 상속
    """
    사용자 소모품 모델은 특정 사용자가 소유한 소모품의 인스턴스를 기록합니다.
    이는 사용자의 소모품 재고 및 사용 이력을 관리합니다.
    """
    __tablename__ = "user_consumables"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 사용자 소모품의 고유 ID
    # user_id는 UserFKMixin으로부터 상속받습니다. (BigInteger)
    # asset_definition_id는 AssetDefinitionFKMixin으로부터 상속받습니다. (BigInteger)
    purchase_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False) # 소모품 구매 일자
    expiration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) # 소모품의 유통기한 (소모성 자재용)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False) # 구매 시점의 소모품 수량
    current_quantity: Mapped[int] = mapped_column(Integer, nullable=False) # 현재 남은 소모품 수량 (소모성 자재용)
    status: Mapped[str] = mapped_column(String(50), default='ACTIVE', nullable=False) # 소모품의 현재 상태 ('ACTIVE', 'USED_UP', 'EXPIRED', 'DISCARDED')
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 소모품에 대한 추가 메모
    
    # --- Relationships ---
    user: Mapped["User"] = relationship("User", back_populates="user_consumables") # 이 소모품을 소유한 사용자 정보
    asset_definition: Mapped["InternalAssetDefinition"] = relationship("InternalAssetDefinition", back_populates="user_consumables") # 이 소모품의 정의 정보
    usage_logs: Mapped[List["ConsumableUsageLog"]] = relationship("ConsumableUsageLog", back_populates="user_consumable") # 이 소모품의 사용 이력 로그들