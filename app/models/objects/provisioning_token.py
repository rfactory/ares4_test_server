from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from app.database import Base
from ..base_model import TimestampMixin, SystemUnitFKMixin

if TYPE_CHECKING:
    from app.models.objects.system_unit import SystemUnit
    # User, Organization import 제거 (더 이상 참조하지 않음)

class ProvisioningToken(Base, TimestampMixin, SystemUnitFKMixin):
    """
    [Object] 기기 프로비저닝 모델 (순수 입장권):
    특정 사용자나 조직에 종속되지 않으며, 오직 '물리적 기기(SystemUnit)'와 'QR 코드'를 연결합니다.
    이 토큰이 검증되면 SystemUnitAssignment 테이블에 소유권이 기록됩니다.
    """
    __tablename__ = "provisioning_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # [1:1 고정] SystemUnitFKMixin의 system_unit_id를 Unique FK로 재정의
    # 하나의 유닛에는 하나의 활성 토큰만 존재해야 하므로 unique=True 유지
    @declared_attr
    def system_unit_id(cls) -> Mapped[int]:
        return mapped_column(BigInteger, ForeignKey("system_units.id"), unique=True, nullable=False)

    # 실제 보안 토큰 값 (QR 데이터)
    token_value: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # 만료 및 사용 여부
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # [수정] used_at은 단순 기록용으로 남겨둠 (관계 설정 X)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # [삭제] issued_by 관련 컬럼들 제거함

    # --- Relationships ---
    
    # 오직 유닛만 바라봅니다.
    system_unit: Mapped["SystemUnit"] = relationship(
        "SystemUnit", 
        back_populates="provisioning_token" # SystemUnit 모델의 변수명과 일치
    )
    
    # [삭제] user, organization 관계 제거함

    def __repr__(self):
        return f"<ProvisioningToken(unit_id={self.system_unit_id}, is_used={self.is_used})>"