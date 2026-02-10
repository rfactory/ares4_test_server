import enum # Python Enum 추가
from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Integer, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin

if TYPE_CHECKING:
    from app.models.objects.device import Device

# 1. 상태를 나타내는 Python Enum 클래스 정의
class BatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class BatchTracking(Base, TimestampMixin, DeviceFKMixin):
    """
    [Event/Log] 배치 처리 추적 모델:
    에지로부터 전송된 대규모 데이터의 처리 상태를 Enum으로 관리합니다.
    """
    __tablename__ = "batch_trackings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    batch_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False, comment="배치 고유 식별자 (UUID)")
    
    total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # 2. String 대신 SQLAlchemy Enum 적용
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_tracking_status", create_type=False), 
        default=BatchStatus.PENDING, 
        nullable=False, 
        comment="진행 상태"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    device: Mapped["Device"] = relationship("Device", back_populates="batch_trackings")

    def __repr__(self):
        return f"<BatchTracking(batch_id={self.batch_id}, status={self.status}, progress={self.processed_count}/{self.total_count})>"