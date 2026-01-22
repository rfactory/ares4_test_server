from sqlalchemy import Column, BigInteger, String, Boolean, Enum, JSON, Integer, ForeignKey # Integer, ForeignKey 추가
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING # TYPE_CHECKING 추가

from app.database import Base
from ..base_model import TimestampMixin

# 런타임 순환 참조 방지 및 타입 힌트 지원
if TYPE_CHECKING:
    from app.models.objects.role import Role

class GovernanceRule(Base, TimestampMixin):
    """
    거버넌스 규칙 모델은 역할 기반 권한 부여 및 시스템 동작을 제어하는 동적 규칙을 정의합니다.
    """
    __tablename__ = "governance_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 규칙의 고유 ID
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True) # 규칙의 식별 가능한 이름
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True) # 규칙에 대한 상세 설명
    
    actor_role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('roles.id'), nullable=False) # 규칙을 트리거하는 행위자 역할 ID
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # 규칙이 적용되는 행동 (예: 'assign_role', 'revoke_role')
    target_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('roles.id'), nullable=True) # 행동의 대상이 되는 역할 ID (선택 사항)
    context: Mapped[str] = mapped_column(Enum('SYSTEM', 'ORGANIZATION', name='governance_context_type', create_type=False), nullable=False) # 규칙이 적용되는 컨텍스트 (SYSTEM, ORGANIZATION)
    allow: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True) # 규칙에 따른 행동 허용 여부 (True: 허용, False: 거부)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100) # 규칙의 우선순위 (낮은 숫자가 높은 우선순위)
    conditions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # 추가적인 복잡한 조건을 정의하는 JSONB 필드

    # Relationships
    actor_role: Mapped["Role"] = relationship("Role", foreign_keys=[actor_role_id]) # 행위자 역할 객체
    target_role: Mapped[Optional["Role"]] = relationship("Role", foreign_keys=[target_role_id]) # 대상 역할 객체