from sqlalchemy import Column, Integer, DateTime, Float, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, HardwareBlueprintFKMixin

class ProductionEvent(Base, TimestampMixin, DeviceFKMixin, HardwareBlueprintFKMixin):
    """
    생산 이벤트 모델: 스마트팜 제품 라인에 특화된 수확 및 재배 관련 이벤트를 기록합니다.
    Naava-like 제품 라인에는 사용되지 않습니다.
    이 테이블은 향후 카메라 비전 기반 이미지 분석 결과(예: YOLO, 이미지 분류)와 연동하여
    식물 성장 상태 평가 및 필요한 조치 식별 기능으로 확장될 수 있도록 설계되었습니다.
    metadata 필드는 이미지 분석 결과를 구조화된 테이블(ImageAnalysis)로 대체하여
    비정형 데이터 통합을 준비합니다.
    """
    __tablename__ = "production_events"

    id = Column(Integer, primary_key=True, index=True) # 생산 이벤트 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다.
    # hardware_blueprint_id는 HardwareBlueprintFKMixin으로부터 상속받습니다.
    event_type = Column(Enum('HARVEST', 'GROWTH_UPDATE', 'MAINTENANCE', name='production_event_type'), nullable=False, default='GROWTH_UPDATE') # 이벤트 유형 (e.g., 'HARVEST' for 수확, 'GROWTH_UPDATE' for 성장 업데이트)
    event_date = Column(DateTime(timezone=True), nullable=False) # 이벤트 발생 시간
    yield_amount = Column(Float, nullable=True) # 수확량 (스마트팜용, Naava-like에서는 Null)
    crop_type = Column(String(50), nullable=True) # 재배 작물 유형 (예: '토마토', '상추')
    growth_stage = Column(String(50), nullable=True) # 성장 단계 (e.g., '발아', '성숙', '수확')
    notes = Column(String(255), nullable=True) # 추가 메모
    # --- Relationships ---
    device = relationship("Device", back_populates="production_events") # 이 생산 이벤트가 발생한 장치 정보
    hardware_blueprint = relationship("HardwareBlueprint", back_populates="production_events") # 이 생산 이벤트와 관련된 하드웨어 블루프린트 정보
    image_analyses = relationship("ImageAnalysis", back_populates="production_event") # 이 생산 이벤트의 이미지 분석 결과 목록