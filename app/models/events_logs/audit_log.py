from sqlalchemy import BigInteger, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING 
from app.database import Base
from ..base_model import TimestampMixin, LogBaseMixin, NullableUserFKMixin, NullableOrganizationFKMixin

# 런타임 순환 참조 방지
if TYPE_CHECKING:
    from app.models.objects.user import User
    from .audit_log_detail import AuditLogDetail
    from app.models.objects.organization import Organization

class AuditLog(Base, TimestampMixin, LogBaseMixin, NullableUserFKMixin, NullableOrganizationFKMixin):
    """
    [Log] 시스템 내 중요한 사용자 활동 및 시스템 이벤트를 기록합니다.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # LogBaseMixin의 event_type을 확장
    event_type: Mapped[str] = mapped_column(
        Enum(
            'DEVICE', 'AUDIT', 'CONSUMABLE_USAGE', 'SERVER_MQTT_CERTIFICATE_ISSUED', 
            'DEVICE_CERTIFICATE_CREATED', 'CERTIFICATE_REVOKED', 
            'SERVER_CERTIFICATE_ACQUIRED_NEW', 'SERVER_CERTIFICATE_REUSED',
            'ORGANIZATION_CREATED', 'ORGANIZATION_UPDATED', 'ORGANIZATION_DELETED', 
            'ACCESS_REQUEST_CREATED', 'ACCESS_REQUEST_UPDATED', 'ACCESS_REQUEST_DELETED',
            'USER_ROLE_ASSIGNED', 'USER_ROLE_REVOKED', 'USER_LOGIN_FAILED',
            name='audit_log_event_type',
            create_type=False# 이름을 명확히 지정
        ), 
        nullable=False, 
        default='AUDIT'
    )

    # --- Relationships ---
    
    # 1. User와의 관계 (NullableUserFKMixin 기반)
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="audit_logs"
    )
    
    # 2. AuditLogDetail과의 관계 (1:N)
    # Mapped[List["..." ]] 스타일로 통일 권장
    details_items: Mapped[List["AuditLogDetail"]] = relationship("AuditLogDetail", back_populates="audit_log", cascade="all, delete-orphan") # 로그 삭제 시 상세 내역도 함께 정리