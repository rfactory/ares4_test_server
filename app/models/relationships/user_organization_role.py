from sqlalchemy import BigInteger, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, UserFKMixin, NullableOrganizationFKMixin, RoleFKMixin

if TYPE_CHECKING:
    from app.models.objects.user import User
    from app.models.objects.organization import Organization
    from app.models.objects.role import Role

class UserOrganizationRole(Base, TimestampMixin, UserFKMixin, NullableOrganizationFKMixin, RoleFKMixin):
    """
    [Relationship] 사용자-조직-역할 관계 모델:
    사용자가 특정 조직 내에서 어떤 권한(Role)을 가졌는지 정의하는 RBAC의 중추입니다.
    조직 ID가 Null인 경우, 플랫폼 전체에 영향을 미치는 시스템 수준의 역할로 간주합니다.
    """
    __tablename__ = "user_organization_roles"
    __table_args__ = (
        # 한 사용자가 한 조직 내에서 동일한 역할을 중복해서 가질 수 없도록 제한
        UniqueConstraint('user_id', 'organization_id', 'role_id', name='_user_org_role_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # --- Relationships (Mapped 적용 완료) ---
    
    # 1. 대상 사용자
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="user_role_assignments"
    )
    
    # 2. 소속 조직 (Null 가능: 시스템 관리자 등)
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", 
        back_populates="user_roles"
    )
    
    # 3. 부여된 역할 (Role 객체)
    role: Mapped["Role"] = relationship(
        "Role", 
        back_populates="users"
    )

    def __repr__(self):
        org_id = self.organization_id if self.organization_id else "SYSTEM"
        return f"<UserOrganizationRole(user={self.user_id}, org={org_id}, role={self.role_id})>"