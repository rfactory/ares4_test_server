from sqlalchemy import BigInteger, String, Text, JSON, Boolean, Integer, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, SystemUnitFKMixin, UserFKMixin, ExecutionMode, ConcurrencyPolicy

if TYPE_CHECKING:
    from app.models.objects.system_unit import SystemUnit
    from app.models.objects.user import User

class TriggerRule(Base, TimestampMixin, SystemUnitFKMixin, UserFKMixin):
    """
    [Instruction Layer] 트리거 규칙 모델:
    현장의 상태(Observation)가 특정 조건(Condition)을 만족할 때 
    정의된 작업(Action)을 즉각 실행하는 '이벤트 기반 제어' 모델입니다.
    """
    __tablename__ = "trigger_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 트리거는 긴급 상황 대응이 많으므로 기본 우선순위를 높게(50) 설정합니다.
    priority: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    
    # 실행 전략 (SET: 특정 상태로 강제 전환 등)
    execution_mode: Mapped[ExecutionMode] = mapped_column(
        Enum(ExecutionMode, name="execution_mode", create_type=False), 
        default=ExecutionMode.ONCE,  # 여기를 ONCE로 수정
        nullable=False
    )
    
    # 사업자의 제어 로직(IP) 보호
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    logic_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    
    timeout_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # 동시성 정책 (REPLACE: 새로운 트리거 발생 시 기존 실행 중인 작업을 교체/갱신)
    concurrency_policy: Mapped[ConcurrencyPolicy] = mapped_column(
        Enum(ConcurrencyPolicy, name="concurrency_policy", create_type=False), 
        default=ConcurrencyPolicy.REPLACE, 
        nullable=False
    )
    
    # [핵심] 트리거 발생 조건 (JSON)
    # 예: {"metric": "temp", "op": ">", "value": 38, "duration_sec": 60}
    condition: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # [핵심] 수행할 작업 (JSON)
    # 예: {"target": "cooling_fan", "cmd": "MAX_SPEED", "params": {"duration": 300}}
    action: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships (Mapped 적용 완료) ---
    system_unit: Mapped["SystemUnit"] = relationship(
        "SystemUnit", back_populates="trigger_rules"
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="trigger_rules"
    )

    def __repr__(self):
        return f"<TriggerRule(name={self.name}, priority={self.priority}, active={self.is_active})>"