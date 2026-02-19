import enum
from sqlalchemy import BigInteger, ForeignKey, Enum, CheckConstraint, Index, event, DateTime, text
from datetime import datetime
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
    OWNER = "OWNER"       # 실질적 소유권
    OPERATOR = "OPERATOR" # 운영권
    VIEWER = "VIEWER"     # 조회권

class SystemUnitAssignment(Base, TimestampMixin):
    """
    [Relationship] 시스템 유닛 할당 모델:
    유닛의 소유 주체(개인/조직)를 결정합니다.
    """
    __tablename__ = "system_unit_assignments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    system_unit_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("system_units.id"), nullable=False, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True, index=True
    )
    organization_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("organizations.id"), nullable=True, index=True
    )
    
    role: Mapped[AssignmentRoleEnum] = mapped_column(
        Enum(AssignmentRoleEnum, name="assignment_role_type", create_type=False), 
        default=AssignmentRoleEnum.OWNER, 
        nullable=False
    )
    
    unassigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True, 
        comment="관계가 종료된 시점. Null이면 현재 소유/이용 중."
)

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND organization_id IS NULL) OR "
            "(user_id IS NULL AND organization_id IS NOT NULL)",
            name="check_exclusive_assignment_subject"
        ),
        # [주인 유일성] 현재 활성화된(unassigned_at IS NULL) 주인은 유닛당 한 명만 존재 가능
        Index(
            "ix_unique_active_unit_owner",
            "system_unit_id",
            unique=True,
            postgresql_where=text("role = 'OWNER' AND unassigned_at IS NULL")
        ),
    )

# --- Relationships ---
    system_unit: Mapped["SystemUnit"] = relationship("SystemUnit", back_populates="assignments")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="system_unit_assignments")
    organization: Mapped[Optional["Organization"]] = relationship("Organization", back_populates="system_unit_assignments")

def __repr__(self):
        owner_info = f"user={self.user_id}" if self.user_id else f"org={self.organization_id}"
        return f"<SystemUnitAssignment(unit={self.system_unit_id}, {owner_info}, role={self.role})>"

# --- [이벤트 리스너 영역: 모델 정의 이후 배치] ---

@event.listens_for(SystemUnitAssignment, "before_update")
def close_sub_assignments(mapper, connection, target):
    """
    [시나리오 A 핵심] OWNER의 소유권이 종료(unassigned_at 설정)되면, 
    해당 유닛의 다른 모든 활성 권한(OPERATOR, VIEWER)도 같은 시점에 종료시킵니다.
    """
    # 1. 방금 소유권 종료 시점(unassigned_at)이 입력되었고 역할이 OWNER인 경우
    if target.role == AssignmentRoleEnum.OWNER and target.unassigned_at is not None:
        # 2. 동일한 유닛에 묶인 다른 모든 활성 레코드(unassigned_at IS NULL)를 찾아 동일 시점으로 종료
        connection.execute(
            SystemUnitAssignment.__table__.update()
            .where(SystemUnitAssignment.system_unit_id == target.system_unit_id)
            .where(SystemUnitAssignment.unassigned_at.is_(None))
            .where(SystemUnitAssignment.id != target.id)
            .values(unassigned_at=target.unassigned_at)
        )

@event.listens_for(SystemUnitAssignment, "after_delete")
def cleanup_related_assignments(mapper, connection, target):
    """
    관리자 도구 등에서 레코드가 물리적으로 삭제될 경우를 대비한 안전장치입니다.
    """
    if target.role == AssignmentRoleEnum.OWNER:
        connection.execute(
            SystemUnitAssignment.__table__.delete().where(
                SystemUnitAssignment.system_unit_id == target.system_unit_id
            )
        )