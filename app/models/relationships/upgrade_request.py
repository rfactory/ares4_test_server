# app/models/relationships/upgrade_request.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, text
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin # UserFKMixin 제거

class UpgradeRequest(Base, TimestampMixin): # UserFKMixin 제거
    """
    업그레이드 요청 모델은 사용자가 자신의 계정 또는 서비스 플랜 업그레이드를 요청하는 기록을 저장합니다.
    관리자의 승인 절차를 거칠 수 있습니다.
    """
    __tablename__ = "upgrade_requests"

    id = Column(Integer, primary_key=True, index=True) # 업그레이드 요청의 고유 ID
    
    # 명시적으로 외래 키 컬럼 정의
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False) # 요청을 시작한 사용자 ID
    
    reason = Column(Text, nullable=True) # 업그레이드 요청 사유
    status = Column(String(20), nullable=False) # 요청의 현재 상태 (예: 'pending', 'approved', 'rejected')
    requested_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False) # 업그레이드 요청이 접수된 시간
    
    # --- 관계 정의 (외래 키) ---
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # 요청을 검토한 관리자 사용자의 ID
    requested_role_id = Column(Integer, ForeignKey("roles.id"), nullable=True) # 요청된 역할의 ID
    
    reviewed_at = Column(DateTime(timezone=True), nullable=True) # 요청이 검토된 시간
    
    # --- Relationships ---
    user = relationship("User", foreign_keys=[user_id], back_populates="upgrade_requests_initiated") # 업그레이드를 요청한 사용자 정보
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by_user_id], back_populates="upgrade_requests_reviewed") # 업그레이드 요청을 검토한 사용자 정보
    requested_role = relationship("Role", foreign_keys=[requested_role_id], back_populates="upgrade_requests") # 요청된 역할 정보