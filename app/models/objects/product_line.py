from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin

class ProductLine(Base, TimestampMixin):
    """
    제품 라인 모델은 회사에서 제공하는 제품의 카테고리를 정의합니다.
    예: 'SmartFarm', 'Naava' 등. 각 제품 라인은 특정 정책을 가질 수 있습니다.
    """
    __tablename__ = "product_lines"

    id = Column(Integer, primary_key=True, index=True) # 제품 라인의 고유 ID
    name = Column(String(100), unique=True, nullable=False) # 제품 라인의 이름 (예: 'SmartFarm', 'Naava')
    description = Column(Text, nullable=True) # 제품 라인에 대한 설명
    enforce_device_limit = Column(Boolean, default=False, nullable=False) # 이 제품 라인에 속한 장치에 대해 장치 수 제한을 강제할지 여부
    
    # --- Relationships ---
    hardware_blueprints = relationship("HardwareBlueprint", back_populates="product_line") # 이 제품 라인에 속하는 하드웨어 블루프린트 목록
