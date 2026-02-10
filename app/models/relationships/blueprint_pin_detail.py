from sqlalchemy import BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin, BlueprintPinMappingFKMixin

if TYPE_CHECKING:
    from ..relationships.blueprint_pin_mapping import BlueprintPinMapping

class BlueprintPinDetail(Base, TimestampMixin, BlueprintPinMappingFKMixin):
    """
    [Object] 블루프린트 핀 상세 정보:
    특정 핀 매핑에 대한 전기적 사양이나 통신 규격(예: 전압 레벨, I2C 주소, 데이터 프로토콜)을 저장합니다.
    하드웨어 제어 로직을 생성하는 AI 에이전트의 기술적 참조 데이터로 활용됩니다.
    """
    __tablename__ = "blueprint_pin_details"
    __table_args__ = (
        # 특정 핀 매핑 내에서 키값 중복 방지 (예: 한 핀에 'voltage'가 두 개일 수 없음)
        UniqueConstraint('blueprint_pin_mapping_id', 'detail_key', name='_pin_detail_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 상속받은 blueprint_pin_mapping_id를 통해 상위 매핑 정보와 연결
    
    # 세부 정보 속성 (예: 'voltage_level', 'protocol', 'pull_up_down')
    detail_key: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 세부 정보 값 (예: '3.3V', 'I2C', 'PULL_UP')
    detail_value: Mapped[str] = mapped_column(Text, nullable=False)
    
    # --- Relationships (Mapped 적용 완료) ---
    # 이 상세 정보가 속한 핀 매핑 객체
    blueprint_pin_mapping: Mapped["BlueprintPinMapping"] = relationship(
        "BlueprintPinMapping", 
        back_populates="pin_details"
    )

    def __repr__(self):
        return f"<BlueprintPinDetail(key={self.detail_key}, value={self.detail_value})>"