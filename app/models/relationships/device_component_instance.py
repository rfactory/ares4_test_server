from sqlalchemy import String, Text, UniqueConstraint, BigInteger, text, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List, TYPE_CHECKING

from app.database import Base
from ..base_model import TimestampMixin, DeviceFKMixin, SupportedComponentFKMixin

if TYPE_CHECKING:
    from ..objects.device import Device
    from ..objects.supported_component import SupportedComponent
    from .device_component_pin_mapping import DeviceComponentPinMapping

class DeviceComponentInstance(Base, TimestampMixin, DeviceFKMixin, SupportedComponentFKMixin):
    """
    [Relationship] 장치 부품 인스턴스:
    특정 기기(RPi 등)에 실제로 장착된 부품의 '실체'와 '공간적 위치'를 정의합니다.
    """
    __tablename__ = "device_component_instances"
    __table_args__ = (
        UniqueConstraint(
            'device_id', 'supported_component_id', 'instance_name', 
            name='_device_component_instance_uc'
        ),
        # 1. 함수형 인덱스: 표현식 전체를 괄호로 한 번 더 감싸 안정성 확보
        Index(
            'ix_unique_spatial_slot',
            text("((spatial_context->'grid'->>'row')), ((spatial_context->'grid'->>'col')), ((spatial_context->'grid'->>'layer'))"),
            unique=True
        ),
        # 2. CheckConstraint: '?' 연산자를 '??'로 이스케이프하여 드라이버 에러 방지
        CheckConstraint(
            "spatial_context ?? 'grid'",
            name='check_spatial_context_has_grid'
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    instance_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True) 
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 공간 정보 및 로컬 SLA (운영 가이드라인)
    spatial_context: Mapped[dict] = mapped_column(
        JSONB, 
        nullable=False, 
        default=lambda: {"grid": {"row": 0, "col": 0, "layer": 0}, "physical": {"x": 0.0, "y": 0.0, "z": 0.0}},
        server_default=text("'{}'"),
        comment="grid(좌표), physical(실측), operating_limits(SLA) 포함"
    )

    # --- Relationships ---
    device: Mapped["Device"] = relationship(
        "Device", back_populates="component_instances"
    )
    supported_component: Mapped["SupportedComponent"] = relationship(
        "SupportedComponent", back_populates="device_component_instances"
    )
    pin_mappings: Mapped[List["DeviceComponentPinMapping"]] = relationship(
        "DeviceComponentPinMapping", 
        back_populates="device_component_instance",
        cascade="all, delete-orphan"
    )