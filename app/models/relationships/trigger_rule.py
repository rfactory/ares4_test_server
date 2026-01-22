from sqlalchemy import BigInteger, String, Text, JSON, Boolean, Column # Column 추가
from sqlalchemy.orm import relationship, Mapped, mapped_column # Mapped, mapped_column 추가
from typing import Optional # Optional 추가
from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, UserFKMixin

class TriggerRule(Base, TimestampMixin, DeviceFKMixin, UserFKMixin):
    """
    트리거 규칙 모델은 특정 장치에서 발생하는 조건에 따라
    자동으로 특정 작업을 수행하도록 정의합니다.
    """
    __tablename__ = "trigger_rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 트리거 규칙의 고유 ID
    # device_id는 DeviceFKMixin으로부터 상속받습니다. (BigInteger)
    # user_id는 UserFKMixin으로부터 상속받습니다. (BigInteger)
    name: Mapped[str] = mapped_column(String(100), nullable=False) # 트리거 규칙의 이름
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 트리거 규칙에 대한 설명
    condition: Mapped[dict] = mapped_column(JSON, nullable=False) # 트리거 발생 조건 (JSON 형식, 예: {'metric': 'humidity', 'operator': '<', 'value': 40})
    action: Mapped[dict] = mapped_column(JSON, nullable=False) # 트리거 발생 시 수행할 작업 (JSON 형식, 예: {'component_id': 2, 'action': 'turn_on'})
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # 트리거 규칙의 활성화 여부
    
    # --- Relationships ---
    device = relationship("Device", back_populates="trigger_rules") # 이 트리거 규칙이 적용되는 장치 정보
    user = relationship("User", back_populates="trigger_rules") # 이 트리거 규칙을 생성하거나 관리하는 사용자 정보
