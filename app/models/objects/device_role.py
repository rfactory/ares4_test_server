# app/models/objects/device_role.py
from sqlalchemy import BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING # TYPE_CHECKING 추가
from app.database import Base
from ..base_model import TimestampMixin

# 런타임 순환 참조 방지 및 타입 힌트 지원
if TYPE_CHECKING:
    from app.models.relationships.device_role_assignment import DeviceRoleAssignment

class DeviceRole(Base, TimestampMixin):
    """
    [Object] 기기가 수행할 수 있는 논리적 역할(예: Vision, Sensor Hub, Controller)의 정의입니다.
    역할 자체를 객체화하여 하드웨어 사양에 관계없이 기능을 유연하게 할당할 수 있게 합니다.
    """
    __tablename__ = "device_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 역할의 고유 ID
    role_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) # 역할 식별 키 (예: 'VISION_NODE')
    display_name: Mapped[str] = mapped_column(String(100), nullable=False) # 사용자에게 보여줄 이름 (예: '비전 분석 노드')
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 역할에 대한 상세 설명

    # --- Relationships ---
    # 이 역할을 부여받은 기기들과의 연결 관계 (N:M)
    assignments: Mapped[List["DeviceRoleAssignment"]] = relationship("DeviceRoleAssignment", back_populates="role")
