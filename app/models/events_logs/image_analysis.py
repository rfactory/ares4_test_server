from sqlalchemy import Column, Integer, DateTime, Float, String, JSON, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional # Added Optional
from datetime import datetime # Added datetime

from app.database import Base
from ..base_model import TimestampMixin, ProductionEventFKMixin  # ProductionEvent 연동 Mixin

class ImageAnalysis(Base, TimestampMixin, ProductionEventFKMixin):
    """
    이미지 분석 모델: 카메라 비전(YOLO/분류) 결과를 저장. ProductionEvent와 연동해 식물 상태 평가/필요 조치 식별.
    비정형 이미지 파일은 외부 URL로 참조.
    """
    __tablename__ = "image_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) # 이미지 분석 ID
    # production_event_id = ProductionEventFKMixin으로부터 상속 (nullable=False).
    analysis_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False) # 분석 시간
    image_url: Mapped[str] = mapped_column(String(255), nullable=False) # 이미지 파일 URL (S3/GCS 등 외부 스토리지)
    detected_disease: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # 감지된 질병/문제 (e.g., 'mildew')
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # 분석 신뢰도 (0.0 ~ 1.0)
    recommended_action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # 권장 조치 (e.g., 'add_fungicide')
    analysis_type: Mapped[str] = mapped_column(Enum('YOLO', 'CLASSIFICATION', 'OTHER', name='analysis_type', create_type=False), nullable=False, default='YOLO') # 분석 유형(defalut yolo는 고민해봐야 함)
    analysis_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # 추가 결과 (e.g., {'bounding_boxes': [...]} – 최소 JSON 사용)
    # --- Relationships ---
    production_event = relationship("ProductionEvent", back_populates="image_analyses") # 이 분석이 속한 생산 이벤트 정보