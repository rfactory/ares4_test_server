# app/models/objects/registration_request.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, text
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin # NullableUserFKMixin, NullableRoleFKMixin 제거
class RegistrationRequest(Base, TimestampMixin): # Mixin 상속 제거
    """
    사용자 등록 요청을 관리하는 모델입니다.
    새로운 사용자가 시스템에 가입을 요청할 때 생성되며, 관리자의 승인을 기다립니다.
    """
    __tablename__ = "registration_requests"
    id = Column(Integer, primary_key=True, index=True) # 등록 요청의 고유 ID
    username = Column(String(50), unique=True, nullable=False) # 요청된 사용자 이름
    email = Column(String(255), unique=True, nullable=False) # 요청된 이메일 주소
    password_hash = Column(String(255), nullable=False) # 요청된 비밀번호의 해시 값
    requested_at = Column(DateTime(timezone=True), server_default=text("now()"), nullable=False) # 등록 요청이 접수된 시간
    status = Column(String(20), default="pending", nullable=False) # 요청의 현재 상태 (예: 'pending', 'approved', 'rejected')
   
    # 명시적으로 외래 키 컬럼 정의
    approved_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # 요청을 승인한 사용자 ID
    requested_role_id = Column(Integer, ForeignKey('roles.id'), nullable=True) # 요청된 역할 ID
   
    approved_at = Column(DateTime(timezone=True), nullable=True) # 요청이 승인된 시간
    rejection_reason = Column(Text, nullable=True) # 요청이 거부된 경우의 사유
   
    # --- Relationships ---
    approved_by_user = relationship("User", foreign_keys=[approved_by_user_id]) # 요청을 승인한 사용자 정보
    requested_role = relationship("Role", foreign_keys=[requested_role_id]) # 요청된 역할 정보