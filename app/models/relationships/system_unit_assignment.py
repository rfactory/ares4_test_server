import enum
from sqlalchemy import BigInteger, ForeignKey, Enum, CheckConstraint, Index, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING

from app.database import Base
from ..base_model import TimestampMixin

# 순환 참조 방지를 위한 타입 체킹
if TYPE_CHECKING:
    from app.models.objects.user import User
    from app.models.objects.organization import Organization
    from app.models.objects.system_unit import SystemUnit

class AssignmentRoleEnum(str, enum.Enum):
    OWNER = "OWNER"       # 실질적 소유권 (삭제 시 하위 권한 동반 삭제 트리거)
    OPERATOR = "OPERATOR" # 운영권
    VIEWER = "VIEWER"     # 조회권

class SystemUnitAssignment(Base, TimestampMixin):
    """
    [Relationship] 시스템 유닛 할당 모델:
    유닛의 소유 주체(개인/조직)를 결정합니다.
    [핵심 로직] OWNER 역할의 레코드가 삭제되면, 해당 유닛의 모든 권한 데이터가 함께 소거됩니다.
    """
    __tablename__ = "system_unit_assignments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 대상 유닛
    system_unit_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("system_units.id"), nullable=False, index=True
    )
    
    # [소유 주체] XOR 제약을 위해 둘 다 Nullable
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True, index=True
    )
    organization_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("organizations.id"), nullable=True, index=True
    )
    
    # 역할 (OWNER/OPERATOR/VIEWER)
    role: Mapped[AssignmentRoleEnum] = mapped_column(
        Enum(AssignmentRoleEnum, name="assignment_role_type", create_type=False), 
        default=AssignmentRoleEnum.OWNER, 
        nullable=False
    )

    __table_args__ = (
        # 1. [XOR 강제] 유저 혹은 조직 중 하나만 주인/권한자가 될 수 있음
        CheckConstraint(
            "(user_id IS NOT NULL AND organization_id IS NULL) OR "
            "(user_id IS NULL AND organization_id IS NOT NULL)",
            name="check_exclusive_assignment_subject"
        ),
        # 2. [주인 유일성] 유닛당 'OWNER'는 무조건 한 명(혹은 0명)만 존재
        Index(
            "ix_unique_unit_owner_constraint",
            "system_unit_id",
            unique=True,
            postgresql_where=(role == 'OWNER')
        ),
    )

    # --- Relationships ---
    system_unit: Mapped["SystemUnit"] = relationship(
        "SystemUnit", back_populates="assignments"
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="system_unit_assignments"
    )
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="system_unit_assignments"
    )

    def __repr__(self):
        owner_info = f"user={self.user_id}" if self.user_id else f"org={self.organization_id}"
        return f"<SystemUnitAssignment(unit={self.system_unit_id}, {owner_info}, role={self.role})>"

# --- 핵심: 자동 연쇄 삭제(Cascade) 트리거 로직 ---

@event.listens_for(SystemUnitAssignment, "after_delete")
def cleanup_related_assignments(mapper, connection, target):
    """
    OWNER 권한을 가진 레코드가 삭제되면(판매/소유권 포기), 
    해당 유닛에 붙어있던 모든 Viewer/Operator 권한을 DB에서 즉시 소거합니다.
    """
    if target.role == AssignmentRoleEnum.OWNER:
        # 동일한 system_unit_id를 가진 모든 할당 정보 삭제
        connection.execute(
            SystemUnitAssignment.__table__.delete().where(
                SystemUnitAssignment.system_unit_id == target.system_unit_id
            )
        )