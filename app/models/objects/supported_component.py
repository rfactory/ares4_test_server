from sqlalchemy import Column, BigInteger, String, Text
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin

class SupportedComponent(Base, TimestampMixin):
    """
    지원되는 컴포넌트 모델은 시스템에서 인식하고 상호 작용할 수 있는
    다양한 유형의 하드웨어 또는 소프트웨어 컴포넌트를 정의합니다.
    이는 장치에 연결될 수 있는 센서, 액추에이터, 모듈 등을 포함합니다.
    """
    __tablename__ = "supported_components"

    id = Column(BigInteger, primary_key=True, index=True) # 지원되는 컴포넌트의 고유 ID
    component_type = Column(String(255), unique=True, nullable=False, index=True) # 컴포넌트의 고유 식별자 (예: 'DHT11_Temperature_Sensor')
    display_name = Column(String(255), nullable=False) # 사용자에게 표시될 컴포넌트 이름 (예: 'DHT11 온도 센서')
    category = Column(String(50), nullable=False) # 컴포넌트의 분류 (예: '센서', '액추에이터', '통신 모듈')
    description = Column(Text, nullable=True) # 컴포넌트에 대한 상세 설명
    telemetry_category = Column(String(50), nullable=True) # 이 컴포넌트가 생성하는 텔레메트리 데이터의 카테고리 (예: '온도', '습도')
    
    # --- Relationships ---
    blueprint_pin_mappings = relationship("BlueprintPinMapping", back_populates="supported_component") # 이 컴포넌트가 사용되는 블루프린트 핀 매핑 목록
    device_component_instances = relationship("DeviceComponentInstance", back_populates="supported_component") # 이 컴포넌트 유형의 장치 컴포넌트 인스턴스 목록
    metadata_items = relationship("SupportedComponentMetadata", back_populates="supported_component") # 이 컴포넌트의 메타데이터 항목 목록