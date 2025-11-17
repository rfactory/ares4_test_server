# app/models/internal/internal_asset_purchase_record.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, AssetDefinitionFKMixin # NullableUserFKMixin 제거
class InternalAssetPurchaseRecord(Base, TimestampMixin, AssetDefinitionFKMixin): # Mixin 상속 제거
    """
    내부 자산 구매 기록 모델은 회사에서 자산을 구매한 내역을 기록합니다.
    이는 재고 관리 및 비용 추적에 사용됩니다.
    """
    __tablename__ = "internal_asset_purchase_records"
    id = Column(Integer, primary_key=True, index=True) # 구매 기록의 고유 ID
    # asset_definition_id는 AssetDefinitionFKMixin으로부터 상속받습니다.
    quantity = Column(Integer, nullable=False) # 구매 수량
    purchase_price_per_unit = Column(Float, nullable=False) # 단위당 구매 가격
    supplier_name = Column(String(255), nullable=False) # 공급업체 이름
    purchase_date = Column(DateTime(timezone=True), nullable=False) # 구매 일자
    invoice_number = Column(String(255), nullable=True) # 관련 송장 번호
    notes = Column(Text, nullable=True) # 구매 기록에 대한 추가 메모
   
    # 명시적으로 외래 키 컬럼 정의
    recorded_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # 구매 기록을 입력한 사용자 ID
   
    # --- Relationships ---
    asset_definition = relationship("InternalAssetDefinition", back_populates="purchase_records") # 구매된 자산의 정의 정보
    recorded_by_user = relationship("User", foreign_keys=[recorded_by_user_id]) # 구매 기록을 입력한 사용자 정보