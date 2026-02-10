from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    from app.models.objects.device import Device
    from app.models.objects.user import User

class ProvisioningToken(Base, TimestampMixin):
    """
    [Object] 기기 프로비저닝 모델:
    기기의 최초 신원 확인 및 mTLS 인증서 발급을 위한 일회용 보안 토큰을 관리합니다.
    """
    __tablename__ = "provisioning_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 특정 기기와 1:1 연결 (unique=True)
    device_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("devices.id"), unique=True, nullable=False
    )
    
    # 실제 보안 토큰 값 (보안을 위해 인덱싱)
    token_value: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    
    # 만료 및 사용 여부
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 토큰을 발급한 관리자 (추적성)
    issued_by_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    # --- Relationships (Mapped 적용 완료) ---
    
    # 1:1 관계 (Device 모델에서 uselist=False 설정 필요)
    device: Mapped["Device"] = relationship(
        "Device", back_populates="provisioning_token"
    )
    
    # 발급자 정보
    issued_by_user: Mapped[Optional["User"]] = relationship(
        "User", 
        foreign_keys=[issued_by_user_id],
        back_populates="issued_provisioning_tokens"
    )

    def __repr__(self):
        return f"<ProvisioningToken(device_id={self.device_id}, is_used={self.is_used})>"