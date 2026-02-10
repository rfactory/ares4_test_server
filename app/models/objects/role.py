import enum
from sqlalchemy import BigInteger, String, Text, UniqueConstraint, Enum, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, NullableOrganizationFKMixin

if TYPE_CHECKING:
    from app.models.objects.organization import Organization
    from app.models.relationships.role_permission import RolePermission
    from app.models.relationships.user_organization_role import UserOrganizationRole
    from app.models.objects.access_request import AccessRequest

# 1. 역할 범위를 위한 Enum 클래스 정의
class RoleScope(str, enum.Enum):
    SYSTEM = 'SYSTEM'             # 전역 역할 (슈퍼 어드민 등)
    ORGANIZATION = 'ORGANIZATION' # 특정 조직 내 역할

class Role(Base, TimestampMixin, NullableOrganizationFKMixin):
    """
    [Object] 역할 모델:
    사용자에게 부여될 권한 그룹을 정의합니다. 
    계층(Tier)과 계보(Lineage)를 통해 복잡한 조직 구조를 표현할 수 있습니다.
    """
    __tablename__ = "roles"
    __table_args__ = (
        # 동일 조직 내에서는 역할 이름이 중복될 수 없음
        UniqueConstraint('organization_id', 'name', name='_organization_role_name_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) 
    
    # 역할 명칭 (예: 'OWNER', 'MAINTAINER', 'VIEWER')
    name: Mapped[str] = mapped_column(String(50), nullable=False, index=True) 
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) 
    
    # 역할의 영향 범위 (Enum 적용)
    scope: Mapped[RoleScope] = mapped_column(
        Enum(RoleScope, name='role_scope', create_type=False), 
        default=RoleScope.ORGANIZATION, 
        nullable=False
    ) 

    # --- 권한 계층 및 관리 로직 ---
    # 계층: 숫자가 낮을수록 강력한 권한 (예: 0: Root, 10: Admin, 100: User)
    tier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True) 
    
    # 계보: 역할 간의 상속 관계 표현 (예: 'ROOT > ORG_ADMIN')
    lineage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) 
    
    # 순서: UI에서 역할을 보여줄 정렬 순서
    numbering: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) 
    
    # 정원 제한: 특정 역할(예: '조직장')의 최대 인원 설정
    max_headcount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) 
    
    # --- Relationships (Mapped 스타일 적용 완료) ---

    # 1. 권한 계층
    permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    ) 
    
    # 2. 조직 계층 (NullableOrganizationFKMixin 상속)
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="roles"
    ) 
    
    # 3. 사용자 및 요청 계층
    users: Mapped[List["UserOrganizationRole"]] = relationship(
        "UserOrganizationRole", back_populates="role"
    ) 
    access_requests: Mapped[List["AccessRequest"]] = relationship(
        "AccessRequest", back_populates="requested_role"
    )
    
    @property
    def is_system_role(self) -> bool:
        """이 역할이 시스템(전역) 역할인지 여부를 반환합니다."""
        # scope가 SYSTEM이거나, organization_id가 없는 경우를 시스템 역할로 간주
        return self.scope == RoleScope.SYSTEM or self.organization_id is None
    
    def __repr__(self):
        return f"<Role(name={self.name}, scope={self.scope}, tier={self.tier})>"