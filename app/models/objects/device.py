# app/models/objects/device.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UUID, Index
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin, OrganizationFKMixin, HardwareBlueprintFKMixin

import enum

class DeviceStatusEnum(enum.Enum):
    UNKNOWN = "UNKNOWN"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    TIMEOUT = "TIMEOUT"

class Device(Base, TimestampMixin, OrganizationFKMixin, HardwareBlueprintFKMixin):
    """
    장치 모델은 시스템에 등록된 각 하드웨어 장치의 고유한 식별 정보와 상태를 관리합니다.
    """
    __tablename__ = "devices"
    __table_args__ = (
        Index('idx_device_org_blueprint', 'organization_id', 'hardware_blueprint_id'), # Added composite index
    )

    id = Column(Integer, primary_key=True, index=True) # 장치의 고유 ID
    cpu_serial = Column(String(255), unique=True, nullable=False, index=True) # 장치의 CPU 고유 시리얼 번호
    current_uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True) # 장치에 할당된 현재 UUID (Universally Unique Identifier)
    # --- 관계 정의 (외래 키) ---
    # hardware_blueprint_id는 HardwareBlueprintFKMixin으로부터 상속받습니다.
    # organization_id는 OrganizationFKMixin으로부터 상속받습니다.
    
    # --- 인증서 관리 중앙화 (제안 2) ---
    device_certificate_id = Column(Integer, ForeignKey("certificates.id"), unique=True, nullable=True) # 장치 인증서의 ID (선택 사항)
    ca_certificate_id = Column(Integer, ForeignKey("certificates.id"), nullable=True) # 장치에 사용된 CA(인증 기관) 인증서의 ID (선택 사항)

    # --- 추가 속성 ---
    visibility_status = Column(Enum('PRIVATE', 'ORGANIZATION', 'PUBLIC', name='device_visibility'), default='PRIVATE', nullable=False) # 장치의 공개 범위 상태 ('PRIVATE', 'ORGANIZATION', 'PUBLIC')
    status = Column(Enum(DeviceStatusEnum, name='device_status'), default=DeviceStatusEnum.UNKNOWN, nullable=False) # 장치의 현재 온라인/오프라인/타임아웃 상태
    
    # --- 기록 (기존) ---
    last_seen_at = Column(DateTime(timezone=True), nullable=True) # 장치가 마지막으로 시스템에 연결된 시간
    
    # --- Relationships ---
    hardware_blueprint = relationship("HardwareBlueprint", back_populates="devices") # 이 장치의 하드웨어 블루프린트 정보
    organization = relationship("Organization", back_populates="devices") # 이 장치가 속한 조직 정보
    device_certificate = relationship("Certificate", foreign_keys=[device_certificate_id]) # 이 장치에 할당된 고유 인증서
    ca_certificate = relationship("Certificate", foreign_keys=[ca_certificate_id]) # 이 장치에 사용된 CA 인증서
    component_instances = relationship("DeviceComponentInstance", back_populates="device") # 이 장치에 설치된 컴포넌트 인스턴스 목록
    users = relationship("UserDevice", back_populates="device") # 이 장치에 접근 권한이 있는 사용자 목록
    schedules = relationship("Schedule", back_populates="device") # 이 장치와 관련된 스케줄 목록
    alert_rules = relationship("AlertRule", back_populates="device") # 이 장치에 설정된 알림 규칙 목록
    trigger_rules = relationship("TriggerRule", back_populates="device") # 이 장치에 설정된 트리거 규칙 목록
    telemetry_data = relationship("TelemetryData", back_populates="device") # 이 장치에서 수집된 텔레메트리 데이터 기록 목록
    device_logs = relationship("DeviceLog", back_populates="device") # 이 장치에서 발생한 로그 기록 목록
    firmware_updates = relationship("FirmwareUpdate", back_populates="device") # 이 장치에 대한 펌웨어 업데이트 기록 목록
    consumable_replacement_events = relationship("ConsumableReplacementEvent", back_populates="device") # 이 장치와 관련된 소모품 교체 이벤트 기록 목록
    consumable_usage_logs = relationship("ConsumableUsageLog", back_populates="device") # 이 장치와 관련된 소모품 사용 기록 목록
    alert_events = relationship("AlertEvent", back_populates="device") # 이 장치에서 발생한 알림 이벤트 기록 목록
    production_events = relationship("ProductionEvent", back_populates="device") # 이 장치에서 발생한 생산 관리 이벤트 목록
    replacement_events = relationship("InternalComponentReplacementEvent", back_populates="device") # 이 장치와 관련된 컴포넌트 교체 이벤트 목록