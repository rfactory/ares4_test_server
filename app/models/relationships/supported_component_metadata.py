from sqlalchemy import Column, BigInteger, String, Text, UniqueConstraint, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional
from app.database import Base
from ..base_model import TimestampMixin, SupportedComponentFKMixin

class SupportedComponentMetadata(Base, TimestampMixin, SupportedComponentFKMixin):
    """
    지원되는 컴포넌트 메타데이터 모델은 특정 SupportedComponent에 대한 추가 메타데이터를 정의합니다.
    이는 SupportedComponent 모델의 'component_metadata' JSON 컬럼을 구조화하여 관계형 데이터베이스의 이점을 활용합니다.
    """
    __tablename__ = "supported_component_metadata"
    __table_args__ = (
        UniqueConstraint('supported_component_id', 'meta_key', name='_component_meta_uc'), # Changed component_id to supported_component_id
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 컴포넌트 메타데이터의 고유 ID
    # supported_component_id는 SupportedComponentFKMixin으로부터 상속받습니다. (BigInteger)
    meta_key: Mapped[str] = mapped_column(String(100), nullable=False) # 메타데이터의 키 (예: 'status', 'threshold', 'protocol_version')
    meta_value: Mapped[str] = mapped_column(Text, nullable=False) # 메타데이터의 값 (Text로 저장, 타입에 따라 캐스팅)
    meta_value_type: Mapped[str] = mapped_column(Enum('STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'ENUM', 'JSON', name='meta_value_type', create_type=False), nullable=False, default='STRING') # 메타데이터 값의 예상 타입 (e.g., 'BOOLEAN' for online/offline)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 메타데이터에 대한 설명

    # --- Relationships ---
    supported_component = relationship("SupportedComponent", back_populates="metadata_items") # 이 메타데이터가 속한 지원되는 컴포넌트 정보
