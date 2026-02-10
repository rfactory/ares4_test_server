from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, UserFKMixin, DeviceFKMixin

if TYPE_CHECKING:
    from app.models.objects.user import User
    from app.models.objects.device import Device

class UserDevice(Base, TimestampMixin, UserFKMixin, DeviceFKMixin):
    """
    [Relationship] 사용자-장치 관계 모델:
    특정 사용자가 개별 장치에 대해 가지는 접근 권한과 개인화된 설정을 관리합니다.
    조직 차원의 권한과는 별개로, 사용자 개인이 기기를 식별하고 제어하는 기준이 됩니다.
    """
    __tablename__ = "user_devices"
    __table_args__ = (
        # 한 사용자가 동일 장치에 대해 중복 관계를 맺는 것을 방지
        UniqueConstraint('user_id', 'device_id', name='_user_device_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 상속받은 user_id (UserFKMixin)
    # 상속받은 device_id (DeviceFKMixin)

    # 사용자-장치 간의 권한 역할 (예: 'owner', 'manager', 'viewer')
    # 조직 권한과 조합하여 최종 제어 가능 여부를 판단합니다.
    role: Mapped[str] = mapped_column(String(20), default='owner', nullable=False) 
    
    # 사용자가 기기에 부여한 개인적 별칭 (예: "거실 식물 공장")
    nickname: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) 

    # --- Relationships (Mapped 적용 완료) ---
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="devices"
    )
    device: Mapped["Device"] = relationship(
        "Device", 
        back_populates="users"
    )

    def __repr__(self):
        return f"<UserDevice(user_id={self.user_id}, device_id={self.device_id}, nickname={self.nickname})>"