from sqlalchemy import BigInteger, String, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING

from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    from app.models.relationships.plan_applicable_product_line import PlanApplicableProductLine
    from app.models.objects.hardware_blueprint import HardwareBlueprint
    from app.models.objects.system_unit import SystemUnit

class ProductLine(Base, TimestampMixin):
    """
    [Object] 제품 라인 모델:
    시스템의 논리적 설계(Template)를 정의하며, 실제 배포되는 SystemUnit의 모태가 됩니다.
    외형(Enclosure)의 변화를 'revision' 필드로 관리하여 하드웨어 생애주기를 추적합니다.
    """
    __tablename__ = "product_lines"
    
    # 이름과 리비전의 조합으로 제품의 물리적 형태 변화를 엄격히 관리
    __table_args__ = (
        UniqueConstraint('name', 'revision', name='_name_revision_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) 
    
    # 제품군 명칭 (예: 'Ares_SmartFarm_V4', 'Naava_GreenWall')
    name: Mapped[str] = mapped_column(String(100), nullable=False) 
    
    # 하드웨어 외형/구조 리비전 (예: 'Rev.A', '2026.Q1')
    revision: Mapped[str] = mapped_column(String(50), default="1.0", nullable=False) 

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) 
    
    # 해당 제품 라인이 요금제별 기기 수 제한을 받는지 여부
    enforce_device_limit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) 
    
    # --- Relationships (Mapped 스타일 적용 완료) ---

    # 1. 비즈니스 계층: 구독 플랜과의 연결 (N:M 중간 테이블)
    plan_applicable_product_lines: Mapped[List["PlanApplicableProductLine"]] = relationship(
        "PlanApplicableProductLine", back_populates="product_line", cascade="all, delete-orphan"
    )
    
    # 2. 설계 계층: 이 제품군에 속하는 구체적인 하드웨어 명세들
    hardware_blueprints: Mapped[List["HardwareBlueprint"]] = relationship(
        "HardwareBlueprint", back_populates="product_line"
    )
    
    # 3. 인스턴스 계층: 이 설계를 기반으로 현장에 설치된 실제 '왕'들
    system_units: Mapped[List["SystemUnit"]] = relationship(
        "SystemUnit", back_populates="product_line"
    )

    def __repr__(self):
        return f"<ProductLine(name={self.name}, revision={self.revision})>"