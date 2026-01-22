from sqlalchemy import BigInteger, JSON, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column # Mapped, mapped_column 추가
from typing import Optional # Optional 추가 (JSON 때문에 필요할 수 있음)
from app.database import Base
from ..base_model import TimestampMixin, RoleFKMixin, PermissionFKMixin # Mixin 추가

class RolePermission(Base, TimestampMixin, RoleFKMixin, PermissionFKMixin): # Mixin 상속
    """
    역할-권한 관계 모델은 특정 역할이 어떤 권한을 가지는지 정의합니다.
    이는 RBAC(Role-Based Access Control)의 핵심 부분으로,
    역할에 따라 접근 가능한 데이터 컬럼이나 필터 조건을 지정할 수 있습니다.
    """
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='_role_permission_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 역할-권한 관계의 고유 ID
    allowed_columns: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # 이 권한이 허용하는 컬럼 목록 (JSON 형식)
    filter_condition: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # 이 권한에 적용되는 데이터 필터 조건 (JSON 형식)
    
    # --- 관계 정의 (외래 키) ---
    # role_id는 RoleFKMixin으로부터 상속받습니다. (BigInteger)
    # permission_id는 PermissionFKMixin으로부터 상속받습니다. (BigInteger)
    
    # --- Relationships ---
    role = relationship("Role", back_populates="permissions") # 이 관계에 연결된 역할 정보
    permission = relationship("Permission", back_populates="roles") # 이 관계에 연결된 권한 정보