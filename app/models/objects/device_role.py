from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    # N:M 관계를 해소하는 중간 테이블(Assignment) 임포트
    from app.models.relationships.device_role_assignment import DeviceRoleAssignment

class DeviceRole(Base, TimestampMixin):
    """
    [Object] 기기 역할 정의 모델:
    기기가 수행할 수 있는 논리적 기능(Vision, Sensor Hub, Controller 등)을 정의합니다.
    """
    __tablename__ = "device_roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 역할 식별 키 (예: 'VISION_NODE', 'MQTT_BROKER')
    role_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # 사용자에게 표시될 이름 (예: '비전 분석 노드')
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Relationships (Mapped 스타일 완료) ---
    
    # 이 역할을 부여받은 기기들과의 연결 관계 (N:M 중간 테이블 참조)
    # DeviceRoleAssignment 모델의 back_populates="role"과 매칭됩니다.
    assignments: Mapped[List["DeviceRoleAssignment"]] = relationship(
        "DeviceRoleAssignment", 
        back_populates="role",
        cascade="all, delete-orphan" # 역할 삭제 시 할당 정보도 함께 정리
    )

    def __repr__(self):
        return f"<DeviceRole(key={self.role_key}, name={self.display_name})>"