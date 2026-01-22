from sqlalchemy import BigInteger, String, Enum, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING # TYPE_CHECKING 추가
from app.database import Base
from ..base_model import TimestampMixin, OrganizationFKMixin, ProductLineFKMixin, NullableUserFKMixin, NullableSystemUnitFKMixin

# 런타임 순환 참조 방지 및 타입 힌트 지원
if TYPE_CHECKING:
    from app.models.objects.product_line import ProductLine
    from app.models.objects.organization import Organization
    from app.models.objects.user import User
    from app.models.objects.device import Device
    from app.models.events_logs.telemetry_data import TelemetryData
    from app.models.events_logs.unit_activity_log import UnitActivityLog
    from app.models.objects.action_log import ActionLog
    from app.models.objects.vision_feature import VisionFeature
    from app.models.objects.image_registry import ImageRegistry
    from app.models.relationships.organization_subscription import OrganizationSubscription
    from app.models.relationships.user_subscription import UserSubscription
    from app.models.relationships.alert_rule import AlertRule

class SystemUnit(Base, TimestampMixin, OrganizationFKMixin, ProductLineFKMixin, NullableUserFKMixin):
    """
    [Object] 시스템 유닛 (심장)
    여러 장치(Device)를 묶어 하나의 논리적 서비스(예: 클러스터)로 관리합니다.
    구독권과 1:1로 매칭되며, RL 모델이 상태를 관측하고 판단을 내리는 단위입니다.
    """
    __tablename__ = "system_units"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 유닛의 운영 상태 (ACTIVE: 가동, INACTIVE: 중지, MAINTENANCE: 점검, PROVISIONING: 생성중)
    status: Mapped[str] = mapped_column(
        Enum('ACTIVE', 'INACTIVE', 'MAINTENANCE', 'PROVISIONING', name='unit_status'),
        default='PROVISIONING',
        nullable=False
    )

    # 도메인별 가변 설정 (예: 팜의 목표 온도, 공장의 생산 목표량 등)
    # 이 필드는 RL 서버가 'Goal'을 파악할 때 사용됩니다.
    unit_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Relationships ---
    
    # 1. 소속 및 정체성
    product_line: Mapped["ProductLine"] = relationship("ProductLine", back_populates="system_units")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="system_units")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="system_units") # 개인 소유일 경우 (NullableUserFKMixin)

    # 2. 하위 자산 (물리)
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="system_unit")
    
    # 3. 데이터 및 지능 (AI/RL)
    telemetry_data: Mapped[List["TelemetryData"]] = relationship("TelemetryData", back_populates="system_unit")
    unit_activities: Mapped[List["UnitActivityLog"]] = relationship("UnitActivityLog", back_populates="system_unit") # 통합 로그
    action_logs: Mapped[List["ActionLog"]] = relationship("ActionLog", back_populates="system_unit") # RL 판단 기록
    vision_features: Mapped[List["VisionFeature"]] = relationship("VisionFeature", back_populates="system_unit") # AI 분석 특징점
    image_registries: Mapped[List["ImageRegistry"]] = relationship("ImageRegistry", back_populates="system_unit") # 배포 모델/이미지

    # 4. 비즈니스 및 보안
    subscription: Mapped[Optional["OrganizationSubscription"]] = relationship("OrganizationSubscription", back_populates="system_unit", uselist=False)
    user_subscription: Mapped[Optional["UserSubscription"]] = relationship("UserSubscription", back_populates="system_unit", uselist=False)
    alert_rules: Mapped[List["AlertRule"]] = relationship("AlertRule", back_populates="system_unit")
