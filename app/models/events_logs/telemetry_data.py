from sqlalchemy import Column, Integer, String, DateTime, Float, Index
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin

class TelemetryData(Base, TimestampMixin, DeviceFKMixin):
    """
    텔레메트리 데이터 모델은 장치에서 수집된 센서 데이터 및 기타 측정값을 저장합니다.
    이는 장치 모니터링, 분석 및 제어에 사용됩니다.
    """
    __tablename__ = "telemetry_data"
    __table_args__ = (
        Index('idx_telemetry_device_time', 'device_id', 'created_at'), # Added composite index
    )

    id = Column(Integer, primary_key=True, index=True) # 텔레메트리 데이터의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다.
    timestamp = Column(DateTime(timezone=True), nullable=False) # 데이터가 측정된 시간
    metric_name = Column(String(100), nullable=False) # 측정 항목의 이름 (예: 'temperature', 'humidity')
    metric_value = Column(Float, nullable=False) # 측정된 값
    unit = Column(String(20), nullable=True) # 측정 값의 단위 (예: '°C', '%')
    
    # --- Relationships ---
    device = relationship("Device", back_populates="telemetry_data") # 이 텔레메트리 데이터를 생성한 장치 정보
    metadata_items = relationship("TelemetryMetadata", back_populates="telemetry_data") # 이 텔레메트리 데이터에 대한 메타데이터 항목 목록