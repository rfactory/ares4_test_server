from sqlalchemy import Column, BigInteger, String, Text, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional # Added Optional

from app.database import Base
from ..base_model import TimestampMixin

class TelemetryMetadata(Base, TimestampMixin):
    """
    텔레메트리 메타데이터 모델은 특정 TelemetryData에 대한 추가 메타데이터를 정의합니다.
    이는 TelemetryData 모델의 'metadata_json' JSON 컬럼을 구조화하여 관계형 데이터베이스의 이점을 활용합니다.
    """
    __tablename__ = "telemetry_metadata"
    __table_args__ = (
        UniqueConstraint('telemetry_data_id', 'meta_key', name='_telemetry_meta_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 텔레메트리 메타데이터의 고유 ID
    telemetry_data_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("telemetry_data.id"), nullable=False) # 관련 텔레메트리 데이터의 ID
    meta_key: Mapped[str] = mapped_column(String(100), nullable=False) # 메타데이터의 키 (예: 'sensor_location', 'calibration_factor')
    meta_value: Mapped[str] = mapped_column(Text, nullable=False) # 메타데이터의 값 (Text로 저장, 타입에 따라 캐스팅)
    meta_value_type: Mapped[str] = mapped_column(Enum('STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'ENUM', 'JSON', name='metadata_value_type', create_type=False), nullable=False, default='STRING') # 메타데이터 값의 예상 타입
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 메타데이터에 대한 설명

    # --- Relationships ---
    telemetry_data = relationship("TelemetryData", back_populates="metadata_items") # 이 메타데이터가 속한 텔레메트리 데이터 정보
