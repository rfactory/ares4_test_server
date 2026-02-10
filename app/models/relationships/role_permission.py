from sqlalchemy import BigInteger, JSON, UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, RoleFKMixin, PermissionFKMixin

if TYPE_CHECKING:
    from app.models.objects.role import Role
    from app.models.objects.permission import Permission

class RolePermission(Base, TimestampMixin, RoleFKMixin, PermissionFKMixin):
    """
    [Relationship] 역할-권한 관계 모델:
    특정 역할(Role)이 가진 권한(Permission)의 범위와 제약 조건을 정의합니다.
    컬럼 레벨 보안(Column-level Security)과 행 레벨 필터링(Row-level Filtering)을 지원합니다.
    """
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='_role_permission_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 1. 데이터 가시성 제어 (JSONB 권장)
    # 예: {"include": ["id", "name", "status"], "exclude": ["internal_cost"]}
    allowed_columns: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) 
    
    # 2. 데이터 필터링 조건 (JSONB 권장)
    # 예: {"organization_id": "current_user_org_id", "status": "ACTIVE"}
    filter_condition: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) 
    
    # --- Relationships ---
    role: Mapped["Role"] = relationship("Role", back_populates="permissions")
    permission: Mapped["Permission"] = relationship("Permission", back_populates="roles")
    
    # --- Association Proxies (개발 편의성) ---
    # rp.permission_name 만으로도 연결된 권한의 이름을 바로 가져올 수 있습니다.
    permission_name: AssociationProxy[str] = association_proxy("permission", "name")
    permission_description: AssociationProxy[str] = association_proxy("permission", "description")

    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission={self.permission_name})>"