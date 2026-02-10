from sqlalchemy import BigInteger, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    # Organization 모델과의 순환 참조 방지
    from .organization import Organization

class OrganizationType(Base, TimestampMixin):
    """
    [Object] 조직 유형 모델:
    조직의 성격(기업, 정부기관, 개인 등)을 정의하는 마스터 테이블입니다.
    Ares4 시스템의 멀티테넌시(Multi-tenancy) 정책 결정의 기준이 됩니다.
    """
    __tablename__ = "organization_types"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 유형 이름 (예: 'ENTERPRISE', 'RESEARCH_LAB', 'INDIVIDUAL')
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # --- Relationships (Mapped 적용 완료) ---
    # 이 유형에 속하는 모든 조직들 (1:N)
    organizations: Mapped[List["Organization"]] = relationship(
        "Organization", 
        back_populates="organization_type"
    )

    def __repr__(self):
        return f"<OrganizationType(name={self.name})>"