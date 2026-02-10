from sqlalchemy import BigInteger, String, Text, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING, List, Optional
from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    # RolePermission 중간 테이블과의 관계를 위한 임포트
    from app.models.relationships.role_permission import RolePermission

class Permission(Base, TimestampMixin):
    """
    [Object] 권한 모델:
    시스템 내에서 수행 가능한 구체적인 액션(예: 'device:read', 'user:delete')을 정의합니다.
    """
    __tablename__ = "permissions"

    # 1. Mapped와 mapped_column으로 전환하여 타입 안정성 확보
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 권한 식별자 (예: 'system_unit:reboot')
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # UI에서 권한 리스트를 보여줄 때 그룹핑 기준 (예: '장치 관리', '회계 관리')
    ui_group: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # 시스템 필수 권한 여부 (True인 경우 관리자도 UI에서 수정/삭제 불가)
    is_system_locked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default='false'
    )
    
    # --- Relationships (Mapped 적용 완료) ---
    # RolePermission 중간 테이블을 통해 여러 Role과 연결됨 (N:M)
    roles: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", 
        back_populates="permission",
        cascade="all, delete-orphan" # 권한 정의가 사라지면 할당 정보도 함께 삭제
    )

    def __repr__(self):
        return f"<Permission(name={self.name}, ui_group={self.ui_group})>"