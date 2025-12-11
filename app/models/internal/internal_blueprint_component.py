from sqlalchemy import Column, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, HardwareBlueprintFKMixin, AssetDefinitionFKMixin # Mixin 추가

class InternalBlueprintComponent(Base, TimestampMixin, HardwareBlueprintFKMixin, AssetDefinitionFKMixin): # Mixin 상속
    """
    내부 블루프린트 컴포넌트 모델은 특정 하드웨어 블루프린트를 구성하는 데 필요한
    내부 자산(예: 특정 센서, 모듈)의 종류와 수량을 정의합니다.
    """
    __tablename__ = "internal_blueprint_components"
    __table_args__ = (
        UniqueConstraint('hardware_blueprint_id', 'asset_definition_id', name='_blueprint_asset_uc'), # Changed blueprint_id to hardware_blueprint_id
    )

    id = Column(Integer, primary_key=True, index=True) # 블루프린트 컴포넌트의 고유 ID
    # hardware_blueprint_id는 HardwareBlueprintFKMixin으로부터 상속받습니다.
    # asset_definition_id는 AssetDefinitionFKMixin으로부터 상속받습니다.
    quantity = Column(Integer, nullable=False) # 해당 블루프린트에 필요한 자산의 수량
    
    # --- Relationships ---
    blueprint = relationship("HardwareBlueprint", back_populates="internal_blueprint_components") # 이 컴포넌트가 속한 하드웨어 블루프린트 정보
    asset_definition = relationship("InternalAssetDefinition", back_populates="blueprint_components") # 이 컴포넌트가 정의하는 내부 자산 정보
