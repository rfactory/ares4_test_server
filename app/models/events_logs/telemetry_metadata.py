from sqlalchemy import BigInteger, String, Text, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING

from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    # TelemetryData 모델과의 순환 참조 방지
    from .telemetry_data import TelemetryData

class TelemetryMetadata(Base, TimestampMixin):
    """
    [Log] 텔레메트리 메타데이터 모델:
    특정 TelemetryData에 대한 추가 구조화된 메타데이터를 정의합니다.
    센서의 위치, 교정 계수 등 AI 모델이 데이터를 해석하는 데 필요한 맥락을 제공합니다.
    """
    __tablename__ = "telemetry_metadata"
    __table_args__ = (
        UniqueConstraint('telemetry_data_id', 'meta_key', name='_telemetry_meta_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 외래 키: TelemetryData와 1:N 관계
    telemetry_data_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("telemetry_data.id"), nullable=False
    )
    
    meta_key: Mapped[str] = mapped_column(String(100), nullable=False)
    meta_value: Mapped[str] = mapped_column(Text, nullable=False)
    
    # meta_value_type: 데이터 파싱 시 캐스팅 가이드 역할
    meta_value_type: Mapped[str] = mapped_column(
        Enum('STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'ENUM', 'JSON', name='metadata_value_type', create_type=False), 
        nullable=False, 
        default='STRING'
    )
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Relationships (Mapped 적용 완료) ---
    # 이 메타데이터가 속한 텔레메트리 데이터 정보
    telemetry_data: Mapped["TelemetryData"] = relationship(
        "TelemetryData", back_populates="metadata_items"
    )