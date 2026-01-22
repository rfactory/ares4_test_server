from sqlalchemy import BigInteger, String, UniqueConstraint, Column # Column 추가
from sqlalchemy.orm import relationship, Mapped, mapped_column # Mapped, mapped_column 추가
from typing import Optional # Optional 추가
from app.database import Base
from ..base_model import TimestampMixin, UserFKMixin, DeviceFKMixin

class UserDevice(Base, TimestampMixin, UserFKMixin, DeviceFKMixin):
    """
    사용자-장치 관계 모델은 특정 사용자가 어떤 장치에 접근 권한을 가지는지 정의합니다.
    사용자와 장치 간의 관계 및 역할을 관리합니다.
    """
    __tablename__ = "user_devices"
    __table_args__ = (
        UniqueConstraint('user_id', 'device_id', name='_user_device_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 사용자-장치 관계의 고유 ID
    # user_id는 UserFKMixin으로부터 상속받습니다. (BigInteger)
    # device_id는 DeviceFKMixin으로부터 상속받습니다. (BigInteger)
    role: Mapped[str] = mapped_column(String(20), default='owner', nullable=False) # 사용자-장치 관계에서의 역할 (예: 'owner', 'viewer')
    nickname: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # 장치에 대한 사용자 지정 별명
    
    # --- Relationships ---
    user = relationship("User", back_populates="devices") # 이 관계에 연결된 사용자 정보
    device = relationship("Device", back_populates="users") # 이 관계에 연결된 장치 정보