import enum
from sqlalchemy import BigInteger, ForeignKey, Boolean, UniqueConstraint, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING
from app.database import Base
from ..base_model import TimestampMixin

if TYPE_CHECKING:
    from app.models.objects.organization import Organization
    from app.models.objects.device import Device

# 관계 유형을 명확히 관리하기 위한 Enum 클래스
class OrgDeviceRelationshipType(str, enum.Enum):
    OWNER = 'OWNER'        # 소유자 (장비 구매/폐기 권한)
    OPERATOR = 'OPERATOR'  # 운영자 (제어/설정 변경 권한)
    VIEWER = 'VIEWER'      # 관찰자 (데이터 조회 전용)

class OrganizationDevice(Base, TimestampMixin):
    """
    [Relationship] 조직-장치 관계 모델:
    특정 조직이 장치에 대해 가지는 권한과 관계의 성격을 정의합니다.
    멀티테넌시 환경에서 장치의 자산 소유권과 운영권을 분리하여 관리합니다.
    """
    __tablename__ = "organization_devices"
    __table_args__ = (
        # 동일 조직 내에서 한 장치에 대해 같은 관계 유형을 중복 설정 방지
        UniqueConstraint('organization_id', 'device_id', 'relationship_type', name='_organization_device_uc'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    
    # 외래 키 설정
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('organizations.id'), nullable=False)
    device_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('devices.id'), nullable=False)
    
    # 관계 유형 (Enum 적용)
    relationship_type: Mapped[OrgDeviceRelationshipType] = mapped_column(
        Enum(OrgDeviceRelationshipType, name='org_device_relationship_type', create_type=False), 
        nullable=False
    )
    
    # 활성화 상태 (Soft Delete 및 일시적 권한 중단 용도)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships (Mapped 적용 완료) ---
    organization: Mapped["Organization"] = relationship(
        "Organization", 
        back_populates="organization_devices"
    )
    device: Mapped["Device"] = relationship(
        "Device", 
        back_populates="organization_devices"
    )

    def __repr__(self):
        return f"<OrganizationDevice(org={self.organization_id}, device={self.device_id}, type={self.relationship_type})>"