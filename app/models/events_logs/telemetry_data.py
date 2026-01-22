from sqlalchemy import Column, BigInteger, String, DateTime, Float, Index, text, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from datetime import datetime
from sqlalchemy.sql import func

from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, SystemUnitFKMixin # SystemUnitFKMixin 추가

class TelemetryData(Base, TimestampMixin, DeviceFKMixin, SystemUnitFKMixin):
    """
    [Log] 텔레메트리 데이터 모델입니다.
    장치에서 수집된 센서 데이터 및 기타 측정값을 저장합니다.
    수조 건의 데이터 속에서도 클러스터 상태를 즉시 조회할 수 있도록 SystemUnit과 연결됩니다.
    """
    __tablename__ = "telemetry_data"
    __table_args__ = (
        Index('idx_telemetry_device_time', 'device_id', 'created_at'), # 기존 인덱스 유지
        Index('idx_telemetry_system_unit_time', 'system_unit_id', 'created_at'), # SystemUnit 별 조회 성능 향상
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 텔레메트리 데이터의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다. (BigInteger)
    # system_unit_id는 SystemUnitFKMixin으로부터 상속받습니다. (BigInteger)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now()) # 데이터가 측정된 시간 (created_at과 동기화)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False) # 측정 항목의 이름 (예: 'temperature', 'humidity')
    metric_value: Mapped[float] = mapped_column(Float, nullable=False) # 측정된 값
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # 측정 값의 단위 (예: '°C', '%')
    
    # --- Relationships ---
    device = relationship("Device", back_populates="telemetry_data") # 이 텔레메트리 데이터를 생성한 장치 정보
    system_unit = relationship("SystemUnit", back_populates="telemetry_data") # 이 텔레메트리 데이터가 속한 시스템 유닛 정보
    metadata_items = relationship("TelemetryMetadata", back_populates="telemetry_data") # 이 텔레메트리 데이터에 대한 메타데이터 항목 목록