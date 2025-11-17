from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin

class Permission(Base, TimestampMixin):
    """
    권한 모델은 시스템 내에서 특정 작업에 대한 접근 제어를 정의합니다.
    각 권한은 고유한 이름을 가지며 역할에 할당될 수 있습니다.
    """
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True) # 권한의 고유 ID
    name = Column(String(100), unique=True, nullable=False, index=True) # 권한의 고유 이름 (예: 'device:read', 'user:create')
    description = Column(Text, nullable=True) # 권한에 대한 설명
    
    # --- Relationships ---
    roles = relationship("RolePermission", back_populates="permission") # 이 권한이 할당된 역할 목록