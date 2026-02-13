from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr # [에러 해결] 꼭 확인하세요!
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from app.database import Base
from ..base_model import TimestampMixin, SystemUnitFKMixin

if TYPE_CHECKING:
    from app.models.objects.system_unit import SystemUnit
    from app.models.objects.user import User
    from app.models.objects.organization import Organization

class ProvisioningToken(Base, TimestampMixin, SystemUnitFKMixin):
    """
    [Object] 기기 프로비저닝 모델:
    [핵심 설계] Device와 직접 연결되지 않음. 
    QR 등록 시 이 토큰을 통해 SystemUnit을 특정하고 사용자를 할당합니다.
    """
    __tablename__ = "provisioning_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # [1:1 고정] SystemUnitFKMixin의 system_unit_id를 Unique FK로 재정의
    @declared_attr
    def system_unit_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey("system_units.id"), unique=True, nullable=False)

    # 실제 보안 토큰 값 (QR 데이터)
    token_value: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # 만료 및 사용 여부
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 발급 주체 정보
    issued_by_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    issued_by_organization_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("organizations.id"), nullable=True)

    # --- Relationships ---
    
    # 1. 유닛과의 1:1 관계 (Device 관계는 완전히 삭제됨)
    system_unit: Mapped["SystemUnit"] = relationship(
        "SystemUnit", 
        back_populates="provisioning_token" # SystemUnit 모델의 단수형 필드와 매칭
    )
    
    # 2. 발급 담당자 및 조직 정보
    issued_by_user: Mapped[Optional["User"]] = relationship(
        "User", 
        foreign_keys=[issued_by_user_id], 
        back_populates="issued_provisioning_tokens"
    )
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", 
        foreign_keys=[issued_by_organization_id], 
        back_populates="provisioning_tokens"
    )

    def __repr__(self):
        return f"<ProvisioningToken(unit_id={self.system_unit_id}, is_used={self.is_used})>"