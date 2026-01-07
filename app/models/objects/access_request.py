# app/models/objects/access_request.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin

class AccessRequest(Base, TimestampMixin):
    """
    사용자의 역할 승격 또는 신규 가입 후 역할 지정을 위한 통합 요청 모델입니다.
    모든 요청은 일단 User 계정이 생성된 후에, 해당 User에 대한 역할 부여를 요청하는 방식으로 통일됩니다.
    """
    __tablename__ = "access_requests"

    id = Column(Integer, primary_key=True, index=True)

    # --- Request Details ---
    reason = Column(Text, nullable=True) # 요청 사유
    type = Column(String(20), default="pull", nullable=False, index=True) # 요청 유형. 'pull'(사용자 요청), 'push'(관리자 초대)

    # --- Requester / Target Info ---
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True) # 요청의 대상이 되는 사용자 ID
    requested_role_id = Column(Integer, ForeignKey('roles.id'), nullable=False, index=True) # 요청된 역할 ID
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True, index=True) # 기업용 요청일 경우, 대상 조직 ID
    initiated_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True) # 'push' 타입 요청에서 초대를 시작한 관리자 ID

    # --- Review Info ---
    status = Column(String(20), default="pending", nullable=False, index=True) # 'pending', 'approved', 'rejected', 'expired', 'completed'
    reviewed_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # --- Verification Info (for final user confirmation) ---
    verification_code = Column(String, nullable=True) # 승인 후, 사용자가 최종 확인에 사용하는 일회용 코드
    verification_code_expires_at = Column(DateTime(timezone=True), nullable=True) # 인증 코드 만료 시간

    # --- Relationships ---
    user = relationship("User", foreign_keys=[user_id], back_populates="access_requests_for_user")
    requested_role = relationship("Role", foreign_keys=[requested_role_id], back_populates="access_requests")
    organization = relationship("Organization") # Simple relationship to get org details
    initiated_by = relationship("User", foreign_keys=[initiated_by_user_id], back_populates="initiated_invitations") # 초대를 시작한 관리자와의 관계
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id], back_populates="reviewed_access_requests")