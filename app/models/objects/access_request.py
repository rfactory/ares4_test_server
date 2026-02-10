import enum
from sqlalchemy import BigInteger, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .role import Role
    from .organization import Organization

# 1. 요청 유형 및 상태를 위한 Enum 정의
class AccessRequestType(str, enum.Enum):
    PULL = "pull"  # 사용자가 직접 권한 요청
    PUSH = "push"  # 관리자가 초대

class AccessRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class AccessRequest(Base, TimestampMixin):
    """
    [Object] 사용자의 역할 승격 또는 신규 가입 후 역할 지정을 위한 통합 요청 모델입니다.
    하나의 요청이 '대상 사용자', '초대자', '검토자' 세 명의 User와 얽힐 수 있습니다.
    """
    __tablename__ = "access_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # --- 요청 상세 정보 ---
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    type: Mapped[AccessRequestType] = mapped_column(
        Enum(AccessRequestType, name="access_request_type", create_type=False),
        default=AccessRequestType.PULL,
        nullable=False,
        index=True
    )
    
    status: Mapped[AccessRequestStatus] = mapped_column(
        Enum(AccessRequestStatus, name="access_request_status", create_type=False),
        default=AccessRequestStatus.PENDING,
        nullable=False,
        index=True
    )

    # --- 외래 키 설정 ---
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=False, index=True)
    requested_role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('roles.id'), nullable=False, index=True)
    organization_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('organizations.id'), nullable=True, index=True)
    initiated_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True, index=True)

    # --- 검토 정보 ---
    reviewed_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- 인증/보안 정보 ---
    verification_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    verification_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Relationships (Mapped 적용 및 다중 외래키 처리) ---
    
    # 1. 대상 사용자 (누구의 권한이 바뀌는가)
    user: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[user_id], 
        back_populates="access_requests_for_user"
    )
    
    # 2. 요청된 역할
    requested_role: Mapped["Role"] = relationship(
        "Role", 
        back_populates="access_requests"
    )
    
    # 3. 소속 조직
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        back_populates="access_requests"
    )
    
    # 4. 요청/초대 시작자 (누가 불렀는가)
    initiated_by: Mapped[Optional["User"]] = relationship(
        "User", 
        foreign_keys=[initiated_by_user_id], 
        back_populates="initiated_invitations"
    )
    
    # 5. 검토자 (누가 승인/거절했는가)
    reviewed_by: Mapped[Optional["User"]] = relationship(
        "User", 
        foreign_keys=[reviewed_by_user_id], 
        back_populates="reviewed_access_requests"
    )