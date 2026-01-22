from sqlalchemy import Column, BigInteger, Boolean, UniqueConstraint, Enum, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column # Mapped, mapped_column 추가
from typing import Optional # Optional 추가 (UniqueConstraint에 필요)
from app.database import Base
from ..base_model import TimestampMixin

class OrganizationDevice(Base, TimestampMixin):
    """
    OrganizationDevice 모델은 특정 조직에 할당된 장치 정보를 나타냅니다.
    이는 조직과 장치 간의 관계를 정의합니다. 관계의 종류(예: 소유, 운영)를 포함합니다.
    """
    __tablename__ = "organization_devices"
    __table_args__ = (
        UniqueConstraint('organization_id', 'device_id', 'relationship_type', name='_organization_device_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 할당의 고유 ID
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('organizations.id'), nullable=False) # 조직 ID
    device_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('devices.id'), nullable=False) # 장치 ID
    relationship_type: Mapped[str] = mapped_column(Enum('OWNER', 'OPERATOR', 'VIEWER', name='org_device_relationship_type', create_type=False), nullable=False) # 조직과 장치 간의 관계 유형 (예: 소유, 운영)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # 할당의 활성화 여부 (Soft delete 용도)

    # --- Relationships ---
    organization = relationship("Organization", back_populates="organization_devices") # 이 할당이 속한 조직 정보
    device = relationship("Device", back_populates="organization_devices") # 이 할당에 연결된 장치 정보