from sqlalchemy import Column, BigInteger, String, Text, JSON, Enum, Integer # Integer (for counts/days)
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional # Added Optional

from app.database import Base
from ..base_model import TimestampMixin

class InternalAssetDefinition(Base, TimestampMixin):
    """
    내부 자산 정의 모델은 회사에서 관리하는 모든 유형의 자산(하드웨어 부품, 소모품 등)에 대한
    일반적인 정의와 속성을 저장합니다.
    """
    __tablename__ = "internal_asset_definitions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 내부 자산 정의의 고유 ID
    
    # --- 자산 종류 구분 ---
    asset_class: Mapped[str] = mapped_column(Enum('HARDWARE_COMPONENT', 'PERISHABLE_GOOD', name='asset_class', create_type=False), nullable=False) # 자산의 분류 (예: 'HARDWARE_COMPONENT', 'PERISHABLE_GOOD')

    # --- 공통 정보 ---
    name: Mapped[str] = mapped_column(String(100), nullable=False) # 자산의 일반적인 이름
    model_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True) # 제조사 모델 번호 (하드웨어의 경우)
    manufacturer: Mapped[str] = mapped_column(String(100), nullable=False) # 제조사 (필수)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 자산에 대한 상세 설명
    category: Mapped[str] = mapped_column(String(50), nullable=False) # 자산의 분류 카테고리 (필수)
    features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # 추가적인 기술적 특성 또는 속성 (JSON 형식)

    # --- '하드웨어 부품' 전용 속성 ---
    pin_connection_type: Mapped[Optional[str]] = mapped_column(Enum('GPIO', 'I2C', 'SPI', 'UART', 'ANALOG', name='pin_connection_type', create_type=False), nullable=True) # 핀 연결 유형 (하드웨어 부품 전용)
    default_pin_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 기본 핀 개수 (하드웨어 부품 전용)
    estimated_lifespan_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 예상 수명 (일 단위, 하드웨어 부품 전용)

    # --- '소모성 자재' 전용 속성 ---
    typical_shelf_life_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 일반적인 유통기한 (일 단위, 소모성 자재 전용)
    
    # --- Relationships ---
    inventory_items = relationship("InternalAssetInventory", back_populates="asset_definition") # 이 자산 정의에 해당하는 재고 품목 목록
    purchase_records = relationship("InternalAssetPurchaseRecord", back_populates="asset_definition") # 이 자산 정의에 대한 구매 기록 목록
    blueprint_components = relationship("InternalBlueprintComponent", back_populates="asset_definition") # 이 자산 정의가 사용되는 블루프린트 컴포넌트 목록
    # InternalComponentReplacementEvent가 UnitActivityLog로 통합되었으므로 관계 제거
    user_consumables = relationship("UserConsumable", back_populates="asset_definition") # 이 자산 정의에 해당하는 사용자 소모품 목록
