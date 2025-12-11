from sqlalchemy import Column, Integer, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, LogBaseMixin, NullableUserFKMixin # Added LogBaseMixin

class AuditLog(Base, TimestampMixin, LogBaseMixin, NullableUserFKMixin): # Inherit LogBaseMixin
    """
    감사 로그 모델은 시스템 내에서 발생하는 중요한 사용자 활동 및 시스템 이벤트를 기록합니다.
    이는 보안 감사, 문제 해결 및 규정 준수에 사용됩니다.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True) # 감사 로그의 고유 ID
    # user_id는 NullableUserFKMixin으로부터 상속받습니다.
    # timestamp는 created_at과 의미가 겹치므로 제거하고 TimestampMixin의 created_at을 사용
    # action은 LogBaseMixin의 description으로 대체됩니다.
    
    # LogBaseMixin의 event_type을 'AUDIT'로 설정
    event_type = Column(Enum('DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', 'SERVER_MQTT_CERTIFICATE_ISSUED', 'DEVICE_CERTIFICATE_CREATED', 'CERTIFICATE_REVOKED', 'SERVER_CERTIFICATE_ACQUIRED_NEW', name='log_event_type'), nullable=False, default='AUDIT') # 로그 유형 (온톨로지 통합 쿼리 용)
    # LogBaseMixin의 log_level을 사용 (AuditLog는 log_level이 명시적으로 필요하지 않을 수 있으므로 nullable=True)
    # LogBaseMixin의 description을 사용 (기존 action 필드 대체)

    # --- Relationships ---
    user = relationship("User", back_populates="audit_logs") # 이 로그를 생성한 사용자 정보 (시스템 작업의 경우 Null)
    details_items = relationship("AuditLogDetail", back_populates="audit_log") # 이 감사 로그에 대한 상세 정보 항목 목록