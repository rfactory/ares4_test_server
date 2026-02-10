import enum
from sqlalchemy import BigInteger, String, Enum, Text, Index, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, NullableUserFKMixin, SystemUnitFKMixin

if TYPE_CHECKING:
    from app.models.objects.device import Device
    from app.models.objects.user import User
    from app.models.objects.system_unit import SystemUnit
    from ..events_logs.observation_snapshot import ObservationSnapshot

# 1. 제어 주체 및 상태 관리를 위한 Enum 정의
class ActorType(str, enum.Enum):
    USER = 'USER'
    RL_AGENT = 'RL_AGENT'
    LLM_MCP = 'LLM_MCP'
    SYSTEM = 'SYSTEM'

class ActionStatus(str, enum.Enum):
    REQUESTED = 'REQUESTED'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    TIMEOUT = 'TIMEOUT'

class ActionLog(Base, TimestampMixin, DeviceFKMixin, NullableUserFKMixin, SystemUnitFKMixin):
    """
    [Object] AI 에이전트나 사용자가 내린 제어 명령 객체:
    결정의 근거(Snapshot)부터 실행 결과까지 기록하여 강화학습의 Reward 계산 및 디버깅에 사용합니다.
    """
    __tablename__ = "action_logs"
    __table_args__ = (
        Index('idx_action_snapshot_id', 'snapshot_id'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # Snapshot과의 연결 (RL의 State-Action 페어링의 핵심)
    snapshot_id: Mapped[Optional[str]] = mapped_column(
        String(255), 
        ForeignKey("observation_snapshots.id"), 
        nullable=True, 
        comment="명령 시점의 상태(이미지+센서) 동기화 키"
    )

    # 명령 주체 (Enum 적용)
    actor_type: Mapped[ActorType] = mapped_column(
        Enum(ActorType, name='actor_type', create_type=False), 
        nullable=False,
        index=True
    )
    
    # RL 모델 식별 (예: 모델 버전 관리용)
    model_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # 제어 명령 및 파라미터
    command: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[Optional[Dict]] = mapped_column(postgresql.JSONB, nullable=True)

    # 실행 결과 피드백
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus, name='action_status', create_type=False),
        default=ActionStatus.REQUESTED,
        nullable=False
    )
    execution_result: Mapped[Optional[Dict]] = mapped_column(
        postgresql.JSONB, 
        nullable=True, 
        comment="장치 피드백, 에러 메시지 등"
    )

    # --- Relationships (Mapped 적용 완료) ---
    
    # 판단 근거가 된 스냅샷 정보
    snapshot: Mapped[Optional["ObservationSnapshot"]] = relationship(
        "ObservationSnapshot", back_populates="action_logs"
    )
    
    # 명령이 수행된 대상 정보
    device: Mapped["Device"] = relationship("Device", back_populates="action_logs")
    system_unit: Mapped["SystemUnit"] = relationship("SystemUnit", back_populates="action_logs")
    
    # 명령을 내린 사용자 (NullableUserFKMixin의 user_id 참조)
    performed_by_user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="action_logs"
    )