from sqlalchemy import Column, BigInteger, DateTime, Float, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column # Mapped, mapped_column 추가
from typing import Optional # Optional 추가
from datetime import datetime # datetime 추가
from sqlalchemy.sql import func # func 추가

from app.database import Base
from ..base_model import TimestampMixin, LogBaseMixin, UserFKMixin, DeviceFKMixin, UserConsumableFKMixin # Added LogBaseMixin

class ConsumableUsageLog(Base, TimestampMixin, LogBaseMixin, UserFKMixin, DeviceFKMixin, UserConsumableFKMixin): # Inherit LogBaseMixin
    """
    [Log] 소모품 사용 로그 모델입니다.
    특정 사용자가 특정 장치에서 소모품을 사용한 기록을 저장하여 소비 패턴 및 재고 관리에 사용됩니다.
    """
    __tablename__ = "consumable_usage_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)  # 소모품 사용 로그의 고유 ID
    # user_id는 UserFKMixin으로부터 상속받습니다. (BigInteger)
    # device_id는 DeviceFKMixin으로부터 상속받습니다. (BigInteger)
    # user_consumable_id는 UserConsumableFKMixin으로부터 상속받습니다. (BigInteger)
    
    usage_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())  # 소모품 사용 날짜 및 시간
    quantity_used: Mapped[float] = mapped_column(Float, nullable=False)  # 사용된 소모품의 수량 (예: 양액 50ml)
    
    # LogBaseMixin의 event_type을 확장하여 사용
    event_type: Mapped[str] = mapped_column(Enum('DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', 'SERVER_MQTT_CERTIFICATE_ISSUED', 'DEVICE_CERTIFICATE_CREATED', 'CERTIFICATE_REVOKED', 'SERVER_CERTIFICATE_ACQUIRED_NEW', name='log_event_type'), nullable=False, default='CONSUMABLE_USAGE')  # 로그 유형 (온톨로지 통합 쿼리 용)
    # LogBaseMixin의 log_level을 사용 (ConsumableUsageLog는 log_level이 명시적으로 필요하지 않을 수 있으므로 nullable=True)
    # LogBaseMixin의 description을 사용 (기존 notes 필드 대체)

    # --- Relationships ---
    user = relationship("User", back_populates="consumable_usage_log_entries") # 소모품을 사용한 사용자 정보
    device = relationship("Device", back_populates="consumable_usage_logs") # 소모품이 사용된 장치 정보
    user_consumable = relationship("UserConsumable", back_populates="usage_logs") # 사용된 소모품 인스턴스 정보