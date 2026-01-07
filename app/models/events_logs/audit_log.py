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
    
    # LogBaseMixin의 event_type을 확장하여 사용
    event_type = Column(Enum(
        'DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', 'SERVER_MQTT_CERTIFICATE_ISSUED', 
        'DEVICE_CERTIFICATE_CREATED', 'CERTIFICATE_REVOKED', 'SERVER_CERTIFICATE_ACQUIRED_NEW',
        'ACCESS_REQUEST_CREATED', 'ACCESS_REQUEST_UPDATED', 'ACCESS_REQUEST_DELETED',
        'USER_ROLE_ASSIGNED', 'USER_ROLE_REVOKED',
        name='log_event_type'), nullable=False, default='AUDIT') # 로그 유형

    # --- Relationships ---
    user = relationship("User", back_populates="audit_logs") # 이 로그를 생성한 사용자 정보 (시스템 작업의 경우 Null)
    details_items = relationship("AuditLogDetail", back_populates="audit_log") # 이 감사 로그에 대한 상세 정보 항목 목록