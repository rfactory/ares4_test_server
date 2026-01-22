from sqlalchemy import BigInteger, UniqueConstraint, Column # Column 추가
from sqlalchemy.orm import relationship, Mapped, mapped_column # Mapped, mapped_column 추가
from typing import Optional # Optional 추가
from app.database import Base
from ..base_model import TimestampMixin, UserFKMixin, OrganizationFKMixin, RoleFKMixin

class UserOrganizationRole(Base, TimestampMixin, UserFKMixin, OrganizationFKMixin, RoleFKMixin):
    """
    사용자-조직-역할 관계 모델은 특정 사용자가 특정 조직 내에서 어떤 역할을 가지는지 정의합니다.
    이는 RBAC(Role-Based Access Control)의 핵심 부분입니다.
    """
    __tablename__ = "user_organization_roles"
    __table_args__ = (
        # 한 사용자는 한 조직 내에서 특정 역할을 한 번만 가질 수 있음
        # organization_id가 NULL인 경우 (시스템 역할)에도 고유성 보장
        UniqueConstraint('user_id', 'organization_id', 'role_id', name='_user_org_role_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 사용자-조직-역할 관계의 고유 ID
    
    # --- 관계 정의 (외래 키) ---
    # user_id는 UserFKMixin으로부터 상속받습니다. (BigInteger)
    # organization_id는 OrganizationFKMixin으로부터 상속받습니다. (BigInteger)
    # role_id는 RoleFKMixin으로부터 상속받습니다. (BigInteger)
    
    # --- Relationships ---
    user = relationship("User", back_populates="user_role_assignments") # 이 관계에 연결된 사용자 정보
    organization = relationship("Organization", back_populates="user_roles") # 이 관계에 연결된 조직 정보 (시스템 역할의 경우 Null)
    role = relationship("Role", back_populates="users") # 이 관계에 연결된 역할 정보