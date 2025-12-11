from sqlalchemy import Column, Integer, String, Text, UniqueConstraint, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional
from app.database import Base
from ..base_model import TimestampMixin, OrganizationFKMixin # OrganizationFKMixin 추가

class Role(Base, TimestampMixin, OrganizationFKMixin): # OrganizationFKMixin 상속
    """
    역할 모델은 사용자에게 부여될 수 있는 권한 그룹을 정의합니다.
    시스템 또는 특정 조직 범위 내에서 역할을 정의할 수 있습니다.
    """
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='_organization_role_name_uc'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) # 역할의 고유 ID
    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # 역할의 이름 (예: '관리자', '사용자')
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 역할에 대한 설명
    scope: Mapped[str] = mapped_column(Enum('SYSTEM', 'ORGANIZATION', name='role_scope', create_type=False), default='ORGANIZATION', nullable=False) # 역할의 적용 범위 ('SYSTEM' 또는 'ORGANIZATION')
    tier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True) # 역할의 계층 (숫자가 낮을수록 높은 권한)
    lineage: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # 역할 계보 (예: 'SYSTEM_ADMIN' -> 'ORG_ADMIN')
    numbering: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 역할의 순서 또는 중요도
    max_headcount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 이 역할의 최대 인원 제한
    
    # --- 관계 정의 (외래 키) ---
    # organization_id는 OrganizationFKMixin으로부터 상속받습니다.
    
    # --- Relationships ---
    permissions = relationship("RolePermission", back_populates="role") # 이 역할에 부여된 권한 목록
    organization = relationship("Organization", back_populates="roles") # 이 역할이 속한 조직 정보 (SYSTEM 역할의 경우 Null)
    users = relationship("UserOrganizationRole", back_populates="role") # 이 역할을 가진 사용자-조직 관계 목록
    access_requests = relationship("AccessRequest", back_populates="requested_role") # 이 역할로의 접근을 요청하는 기록 목록