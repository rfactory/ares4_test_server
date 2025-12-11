from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional # Added Optional

from app.database import Base
from ..base_model import TimestampMixin

class AuditLogDetail(Base, TimestampMixin):
    """
    감사 로그 상세 모델은 특정 AuditLog에 대한 추가 상세 정보를 정의합니다.
    이는 AuditLog 모델의 'details' JSON 컬럼을 구조화하여 관계형 데이터베이스의 이점을 활용합니다.
    """
    __tablename__ = "audit_log_details"
    __table_args__ = (
        UniqueConstraint('audit_log_id', 'detail_key', name='_audit_detail_uc'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) # 감사 로그 상세 정보의 고유 ID
    audit_log_id: Mapped[int] = mapped_column(Integer, ForeignKey("audit_logs.id"), nullable=False) # 관련 감사 로그의 ID
    detail_key: Mapped[str] = mapped_column(String(100), nullable=False) # 상세 정보의 키 (예: 'changed_field', 'old_value', 'new_value')
    detail_value: Mapped[str] = mapped_column(Text, nullable=False) # 상세 정보의 값 (Text로 저장, 타입에 따라 캐스팅)
    detail_value_type: Mapped[str] = mapped_column(Enum('STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'ENUM', 'JSON', name='detail_value_type', create_type=False), nullable=False, default='STRING') # 상세 정보 값의 예상 타입
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 상세 정보에 대한 설명

    # --- Relationships ---
    audit_log = relationship("AuditLog", back_populates="details_items") # 이 상세 정보가 속한 감사 로그 정보
