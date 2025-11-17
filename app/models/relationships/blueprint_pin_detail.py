from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, BlueprintPinMappingFKMixin

class BlueprintPinDetail(Base, TimestampMixin, BlueprintPinMappingFKMixin):
    """
    블루프린트 핀 상세 정보 모델은 특정 블루프린트 핀 매핑에 대한 추가적인 세부 정보를 저장합니다.
    예를 들어, 핀의 전압 레벨, 데이터 프로토콜 등을 정의할 수 있습니다.
    """
    __tablename__ = "blueprint_pin_details"
    __table_args__ = (
        UniqueConstraint('blueprint_pin_mapping_id', 'detail_key', name='_pin_detail_uc'),
    )

    id = Column(Integer, primary_key=True, index=True) # 블루프린트 핀 상세 정보의 고유 ID
    # blueprint_pin_mapping_id는 BlueprintPinMappingFKMixin으로부터 상속받습니다.
    detail_key = Column(String(100), nullable=False) # 핀 세부 정보의 키 (예: 'voltage_level', 'data_protocol')
    detail_value = Column(Text, nullable=False) # 핀 세부 정보의 값
    
    # --- Relationships ---
    blueprint_pin_mapping = relationship("BlueprintPinMapping", back_populates="pin_details") # 이 상세 정보가 속한 블루프린트 핀 매핑 정보