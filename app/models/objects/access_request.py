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

    # --- Requester / Target Info ---
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True) # 요청의 대상이 되는 사용자 ID
    requested_role_id = Column(Integer, ForeignKey('roles.id'), nullable=False, index=True) # 요청된 역할 ID
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True, index=True) # 기업용 요청일 경우, 대상 조직 ID

    # --- Review Info ---
    status = Column(String(20), default="pending", nullable=False, index=True) # 'pending', 'approved', 'rejected'
    reviewed_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # --- Relationships ---
    user = relationship("User", foreign_keys=[user_id], back_populates="access_requests_as_requester")
    requested_role = relationship("Role", foreign_keys=[requested_role_id], back_populates="access_requests")
    organization = relationship("Organization") # Simple relationship to get org details
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by_user_id], back_populates="access_requests_as_reviewer")