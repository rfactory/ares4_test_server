from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin

class OrganizationType(Base, TimestampMixin):
    """
    조직의 유형을 정의하는 모델입니다.
    예: '기업', '정부기관', '개인' 등.
    """
    __tablename__ = "organization_types"

    id = Column(Integer, primary_key=True, index=True) # 조직 유형의 고유 ID
    name = Column(String(50), unique=True, nullable=False) # 조직 유형의 이름 (예: '기업', '정부기관')
    description = Column(String(255), nullable=True) # 조직 유형에 대한 설명
    
    # --- Relationships ---
    organizations = relationship("Organization", back_populates="organization_type") # 이 조직 유형에 속하는 조직 목록