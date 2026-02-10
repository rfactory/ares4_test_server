import enum
from sqlalchemy import BigInteger, String, Boolean, Enum, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    from app.models.objects.role import Role

# 1. 컨텍스트 및 주요 행동을 Enum으로 관리하여 보안 허점 방지
class GovernanceContext(str, enum.Enum):
    SYSTEM = 'SYSTEM'
    ORGANIZATION = 'ORGANIZATION'

class GovernanceRule(Base, TimestampMixin):
    """
    [Object] 거버넌스 규칙 모델:
    누가(Actor Role), 무엇을(Action), 어떤 대상(Target Role)에게 할 수 있는지 정의하는 동적 정책 엔진입니다.
    """
    __tablename__ = "governance_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 규칙 식별 정보
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    
    # 규칙의 주체와 객체
    actor_role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('roles.id'), nullable=False)
    target_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('roles.id'), nullable=True)
    
    # 규칙의 내용
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # 예: 'assign_role', 'access_telemetry'
    
    context: Mapped[GovernanceContext] = mapped_column(
        Enum(GovernanceContext, name='governance_context_type', create_type=False), 
        nullable=False
    )
    
    allow: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100) # 낮을수록 우선순위 높음
    
    # 복잡한 조건식 (예: {"time_range": "09:00-18:00", "ip_range": "..."})
    conditions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # --- Relationships ---
    # 하나의 테이블(Role)을 두 번 참조하므로 foreign_keys 명시
    actor_role: Mapped["Role"] = relationship("Role", foreign_keys=[actor_role_id])
    target_role: Mapped[Optional["Role"]] = relationship("Role", foreign_keys=[target_role_id])

    def __repr__(self):
        return f"<GovernanceRule(name={self.rule_name}, action={self.action}, allow={self.allow})>"