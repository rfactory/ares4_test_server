from sqlalchemy import BigInteger, Enum, JSON, Column # Column, BigInteger, JSON 추가
from sqlalchemy.orm import relationship, Mapped, mapped_column # Mapped, mapped_column 추가
from typing import Optional # Optional 추가
from app.database import Base
from ..base_model import TimestampMixin, LogBaseMixin, DeviceFKMixin # Added LogBaseMixin

class DeviceLog(Base, TimestampMixin, LogBaseMixin, DeviceFKMixin): # Inherit LogBaseMixin
    """
    [Log] 장치 로그 모델입니다.
    특정 장치에서 발생하는 로그 이벤트를 기록하며, 장치 문제 해결 및 모니터링에 사용됩니다.
    """
    __tablename__ = "device_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)  # 장치 로그의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다. (BigInteger)
    # timestamp는 TimestampMixin의 created_at으로 대체됩니다.
    # log_level은 LogBaseMixin으로부터 상속받습니다.
    # description은 LogBaseMixin으로부터 상속받습니다.
    log_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 로그에 대한 추가 메타데이터 (JSON 형식)
    
    # LogBaseMixin의 event_type을 'DEVICE'로 설정 (오버라이드)
    event_type: Mapped[str] = mapped_column(Enum('DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', 'SERVER_MQTT_CERTIFICATE_ISSUED', 'DEVICE_CERTIFICATE_CREATED', 'CERTIFICATE_REVOKED', 'SERVER_CERTIFICATE_ACQUIRED_NEW', name='log_event_type'), nullable=False, default='DEVICE') # 로그 유형 (온톨로지 통합 쿼리 용)

    # --- Relationships ---
    device = relationship("Device", back_populates="device_logs") # 이 로그를 생성한 장치 정보
