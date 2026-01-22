from sqlalchemy import BigInteger, String, JSON, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING # TYPE_CHECKING 추가
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, NullableUserFKMixin, SystemUnitFKMixin

# 런타임 순환 참조 방지 및 타입 힌트 지원
if TYPE_CHECKING:
    from app.models.objects.device import Device
    from app.models.objects.user import User
    from app.models.objects.system_unit import SystemUnit

class ActionLog(Base, TimestampMixin, DeviceFKMixin, NullableUserFKMixin, SystemUnitFKMixin):
    """
    [Object] AI 에이전트나 사용자가 내린 제어 명령 객체입니다.
    명령의 의도(Action)부터 결과(Result)까지의 생애주기를 기록합니다.
    """
    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 명령 주체
    actor_type: Mapped[str] = mapped_column(
        Enum('USER', 'RL_AGENT', 'LLM_MCP', 'SYSTEM', name='actor_type'), 
        nullable=False,
        index=True
    )
    
    # RL 모델 식별 (RL_AGENT인 경우 필수)
    model_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # 제어 명령 및 파라미터
    command: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # --- 실행 결과 피드백 추가 ---
    # 명령의 현재 상태 (REQUESTED, SUCCESS, FAILED, TIMEOUT)
    status: Mapped[str] = mapped_column(
        Enum('REQUESTED', 'SUCCESS', 'FAILED', 'TIMEOUT', name='action_status'),
        default='REQUESTED',
        nullable=False
    )
    # 장치로부터 돌아온 실제 결과 값이나 에러 메시지
    # 예: {"actual_voltage": 12.1}, {"error": "Device offline"}
    execution_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # --- Relationships ---
    device: Mapped["Device"] = relationship("Device", back_populates="action_logs")
    performed_by_user: Mapped[Optional["User"]] = relationship("User", back_populates="action_logs")
    system_unit: Mapped["SystemUnit"] = relationship("SystemUnit", back_populates="action_logs")