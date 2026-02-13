import enum
from sqlalchemy import BigInteger, String, DateTime, Text, JSON, Boolean, Enum, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from app.database import Base
from ..base_model import TimestampMixin, SystemUnitFKMixin, UserFKMixin

# 런타임 순환 참조 방지
if TYPE_CHECKING:
    from app.models.objects.system_unit import SystemUnit
    from app.models.objects.user import User
    from app.models.objects.organization import Organization

class ExecutionMode(str, enum.Enum):
    """
    작업의 실행 성격을 정의합니다.
    """
    ONCE = "ONCE"             # 1회성: 1 Cycle 수행 후 종료
    CONTINUOUS = "CONTINUOUS" # 무한 지속: 명시적 중지 전까지 무한 루프 (데몬)
    INTERVAL = "INTERVAL"     # 주기적: 특정 시간 간격마다 실행
    CRON = "CRON"             # 시각 기반: 특정 시각/날짜마다 실행

class ConcurrencyPolicy(str, enum.Enum):
    """
    이전 작업이 끝나지 않았을 때의 처리 정책입니다.
    """
    SKIP = "SKIP"       # 이번 차례 건너뜀
    FORCED = "FORCED"   # 중복 실행 허용
    REPLACE = "REPLACE" # 기존 작업 종료 후 새로 시작

class Schedule(Base, TimestampMixin, SystemUnitFKMixin, UserFKMixin):
    """
    [Instruction Layer] 스케줄 모델:
    Ares4 시스템의 자동화 실행 지시서입니다. 
    시간 기반 반복뿐만 아니라, 무한 루프 상주 작업 및 1회성 시퀀스 실행을 모두 관리합니다.
    """
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # --- 식별 및 메타데이터 ---
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 우선순위 (0: 최상위/긴급, 99: 최하위)
    priority: Mapped[int] = mapped_column(Integer, default=10, nullable=False) 
    
    # --- 실행 전략 (MP3 MSA 블록 오케스트레이션의 핵심) ---
    execution_mode: Mapped[ExecutionMode] = mapped_column(
        Enum(ExecutionMode, name="execution_mode"), 
        default=ExecutionMode.ONCE, 
        nullable=False
    )
    
    # 지적재산권(IP) 보호: True일 경우 타 사업자나 일반 유저의 수정/열람 제한
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) 
    logic_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    
    # 안전 장치: 단일 실행이 설정된 초를 넘기면 강제 타임아웃
    timeout_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) 
    
    # 중복 실행 방지 정책
    concurrency_policy: Mapped[ConcurrencyPolicy] = mapped_column(
        Enum(ConcurrencyPolicy, name="concurrency_policy"), 
        default=ConcurrencyPolicy.SKIP, 
        nullable=False
    )
    
    # --- 시간 제어 로직 (무한/1회성 판단 기준) ---
    # 작업이 활성화될 수 있는 시작 시점
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # 작업의 유효 종료 시점
    # [중요] end_time이 NULL이면 '무한 반복' 또는 '수동 중지 전까지 지속'을 의미합니다.
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        comment="NULL일 경우 무한 지속(Continuous) 또는 영구 반복을 의미함"
    )
    
    # 반복 패턴 정의 (JSON)
    # 1회성(ONCE): NULL
    # 주기(INTERVAL): {"type": "seconds", "value": 300} -> 5분마다
    # 시각(CRON): {"expression": "0 8 * * *"} -> 매일 08시
    # N회 반복: {"max_cycles": 10} -> 10번 수행 후 자동 종료
    recurrence_pattern: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # --- 실행 내용 (실행 설계도) ---
    # 예: [{"instance_id": 1, "cmd": "START", "args": {"speed": 50}}]
    action_details: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    system_unit: Mapped["SystemUnit"] = relationship(
        "SystemUnit", back_populates="schedules"
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="schedules"
    )
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="schedules"
    )

    def __repr__(self):
        return f"<Schedule(name={self.name}, mode={self.execution_mode}, active={self.is_active})>"