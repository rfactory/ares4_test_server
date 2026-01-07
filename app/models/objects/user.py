from sqlalchemy import Column, Integer, String, DateTime, Boolean, text
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional # Added Optional
from datetime import datetime # Added datetime
from app.database import Base
from ..base_model import TimestampMixin # UserFKMixin is no longer used here but keeping for reference

class User(Base, TimestampMixin):
    """
    사용자 계정 정보를 저장하는 모델입니다.
    인증, 권한 부여 및 다양한 사용자 관련 활동을 관리합니다.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True) # 사용자의 고유 ID
    username = Column(String(50), unique=True, index=True, nullable=False) # 사용자 로그인에 사용되는 고유 사용자 이름
    email = Column(String(255), unique=True, index=True, nullable=False) # 사용자의 고유 이메일 주소
    password_hash = Column(String(255), nullable=False) # 사용자 비밀번호의 해시 값
    last_login = Column(DateTime(timezone=True), nullable=False, server_default=text("now()")) # 사용자의 마지막 로그인 시간
    reset_token = Column(String(255), nullable=True) # 비밀번호 재설정 토큰
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True) # 비밀번호 재설정 토큰 만료 시간
    email_verification_token = Column(String(255), nullable=True) # 이메일 인증 토큰
    email_verification_token_expires_at = Column(DateTime(timezone=True), nullable=True) # 이메일 인증 토큰 만료 시간
    is_active = Column(Boolean, default=True, nullable=False) # 사용자 계정의 활성화 여부
    is_staff = Column(Boolean, default=False, nullable=False) # 관리자 패널 접근 권한 여부
    is_superuser = Column(Boolean, default=False, nullable=False) # 모든 권한을 가진 최고 관리자 여부
    is_two_factor_enabled = Column(Boolean, default=False, nullable=False) # 2단계 인증 활성화 여부
    
    # --- Relationships ---
    user_role_assignments = relationship("UserOrganizationRole", back_populates="user") # 사용자에게 할당된 역할 관계 목록 (조직별 또는 시스템 전반)
    devices = relationship("UserDevice", back_populates="user") # 사용자가 소유하거나 접근 권한이 있는 장치 목록
    schedules = relationship("Schedule", back_populates="user") # 사용자가 생성하거나 관리하는 스케줄 목록
    alert_rules = relationship("AlertRule", back_populates="user") # 사용자가 설정한 알림 규칙 목록
    trigger_rules = relationship("TriggerRule", back_populates="user") # 사용자가 설정한 트리거 규칙 목록
    subscriptions = relationship("UserSubscription", back_populates="user") # 사용자의 구독 정보 목록
    firmware_updates_initiated = relationship("FirmwareUpdate", foreign_keys="FirmwareUpdate.initiated_by_user_id", back_populates="initiated_by_user") # 사용자가 시작한 펌웨어 업데이트 기록 목록
    consumables = relationship("UserConsumable", back_populates="user") # 사용자가 구매하거나 소유한 소모품 목록
    consumable_replacement_events = relationship("ConsumableReplacementEvent", back_populates="user") # 사용자와 관련된 소모품 교체 이벤트 기록 목록
    consumable_usage_logs = relationship("ConsumableUsageLog", back_populates="user") # 사용자와 관련된 소모품 사용 기록 목록
    alert_events_generated = relationship("AlertEvent", foreign_keys="AlertEvent.user_id", back_populates="user") # 사용자에 의해 생성된 알림 이벤트 목록
    alert_events_acknowledged = relationship("AlertEvent", foreign_keys="AlertEvent.acknowledged_by_user_id", back_populates="acknowledged_by_user") # 사용자가 확인한 알림 이벤트 목록
    internal_asset_inventory_updates = relationship("InternalAssetInventory", foreign_keys="InternalAssetInventory.last_updated_by_user_id", back_populates="last_updated_by_user") # 사용자가 마지막으로 업데이트한 내부 자산 재고 항목 목록
    internal_asset_purchase_records = relationship("InternalAssetPurchaseRecord", foreign_keys="InternalAssetPurchaseRecord.recorded_by_user_id", back_populates="recorded_by_user") # 사용자가 기록한 내부 자산 구매 기록 목록
    internal_component_replacement_events = relationship("InternalComponentReplacementEvent", foreign_keys="InternalComponentReplacementEvent.recorded_by_user_id", back_populates="recorded_by_user") # 사용자가 기록한 내부 컴포넌트 교체 이벤트 목록
    audit_logs = relationship("AuditLog", back_populates="user") # 사용자가 생성한 감사 로그 목록

    # New unified access requests relationships
    access_requests_for_user = relationship("AccessRequest", foreign_keys="AccessRequest.user_id", back_populates="user") # 이 사용자가 요청한 접근 요청 목록
    reviewed_access_requests = relationship("AccessRequest", foreign_keys="AccessRequest.reviewed_by_user_id", back_populates="reviewed_by") # 이 사용자가 검토한 접근 요청 목록
    initiated_invitations = relationship("AccessRequest", foreign_keys="AccessRequest.initiated_by_user_id", back_populates="initiated_by") # 이 사용자가 시작한 초대 목록