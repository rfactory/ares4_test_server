from sqlalchemy import Column, BigInteger, String, Text, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING # TYPE_CHECKING 추가

from app.database import Base
from ..base_model import TimestampMixin

# 런타임 순환 참조 방지 및 타입 힌트 지원
if TYPE_CHECKING:
    from app.models.relationships.plan_applicable_product_line import PlanApplicableProductLine
    from app.models.objects.hardware_blueprint import HardwareBlueprint
    from app.models.objects.system_unit import SystemUnit

class ProductLine(Base, TimestampMixin):
    """
    [Object] 제품 라인 모델은 회사에서 제공하는 제품의 카테고리를 정의합니다.
    이제 SystemUnit(클러스터 인스턴스)의 설계도 역할을 하는 상위 개체로 기능하며,
    어떤 구독 플랜에서 어떤 제품 라인을 쓸 수 있는지를 결정하는 핵심 메뉴판의 구성 요소가 됩니다.
    """
    __tablename__ = "product_lines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 제품 라인의 고유 ID
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False) # 제품 라인의 이름 (예: 'SmartFarm', 'Naava')
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 제품 라인에 대한 설명
    enforce_device_limit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) # 이 제품 라인에 속한 장치에 대해 장치 수 제한을 강제할지 여부
    
    # --- Relationships ---
    # N:M 관계: 여러 플랜에 속할 수 있음
    plan_applicable_product_lines: Mapped[List["PlanApplicableProductLine"]] = relationship(
        "PlanApplicableProductLine", back_populates="product_line"
    )
    # 이 제품 라인(클러스터)을 구성하는 개별 하드웨어 설계도들
    hardware_blueprints: Mapped[List["HardwareBlueprint"]] = relationship("HardwareBlueprint", back_populates="product_line")
    
    # 이 설계도(ProductLine)를 기반으로 생성된 실제 라즈베리파이 클러스터들
    system_units: Mapped[List["SystemUnit"]] = relationship("SystemUnit", back_populates="product_line")