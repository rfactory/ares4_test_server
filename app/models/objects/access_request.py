# app/models/objects/access_request.py
from sqlalchemy import BigInteger, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional
from datetime import datetime
from app.database import Base
from ..base_model import TimestampMixin

class AccessRequest(Base, TimestampMixin):
    """
    [Object] 사용자의 역할 승격 또는 신규 가입 후 역할 지정을 위한 통합 요청 모델입니다.
    모든 외래 키는 시스템 확장성을 위해 BigInteger를 사용합니다.
    """
    __tablename__ = "access_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # --- 요청 상세 정보 ---
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 요청 사유
    type: Mapped[str] = mapped_column(String(20), default="pull", nullable=False, index=True) # 'pull'(요청), 'push'(초대)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True) # 'pending', 'approved' 등

    # --- 대상 및 주체 정보 (BigInteger FK) ---
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=False, index=True)
    requested_role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('roles.id'), nullable=False, index=True)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('organizations.id'), nullable=True, index=True)
    initiated_by_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True, index=True)

    # --- 검토 정보 ---
    reviewed_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- 인증 정보 ---
    verification_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    verification_code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    user = relationship("User", foreign_keys=[user_id], back_populates="access_requests_for_user")
    requested_role = relationship("Role", foreign_keys=[requested_role_id], back_populates="access_requests")
    organization = relationship("Organization") 
    initiated_by = relationship("User", foreign_keys=[initiated_by_user_id], back_populates="initiated_invitations")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id], back_populates="reviewed_access_requests")