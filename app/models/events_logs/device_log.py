from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, LogBaseMixin, DeviceFKMixin # Added LogBaseMixin

class DeviceLog(Base, TimestampMixin, LogBaseMixin, DeviceFKMixin): # Inherit LogBaseMixin
    """
    장치 로그 모델은 특정 장치에서 발생하는 로그 이벤트를 기록합니다.
    이는 장치 문제 해결 및 모니터링에 사용됩니다.
    """
    __tablename__ = "device_logs"

    id = Column(Integer, primary_key=True, index=True)  # 장치 로그의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다.
    # timestamp는 TimestampMixin의 created_at으로 대체됩니다.
    # log_level은 LogBaseMixin으로부터 상속받습니다.
    # message는 LogBaseMixin의 description으로 대체됩니다.
    metadata_json = Column(JSON, nullable=True)  # 로그에 대한 추가 메타데이터 (JSON 형식, 예: 에러 코드, 스택 트레이스)
    
    # LogBaseMixin의 event_type을 'DEVICE'로 설정
    event_type = Column(Enum('DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', name='log_event_type'), nullable=False, default='DEVICE') # 로그 유형 (온톨로지 통합 쿼리 용)
    # LogBaseMixin의 log_level을 사용
    # LogBaseMixin의 description을 사용 (기존 message 필드 대체)

    # --- Relationships ---
    device = relationship("Device", back_populates="device_logs") # 이 로그를 생성한 장치 정보
