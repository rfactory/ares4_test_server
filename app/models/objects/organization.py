# app/models/objects/organization.py
from sqlalchemy import Column, BigInteger, String, Boolean, Enum, text, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

from app.database import Base
from ..base_model import TimestampMixin, OrganizationTypeFKMixin

class Organization(Base, TimestampMixin, OrganizationTypeFKMixin):
    """
    [Object] 조직 정보를 저장하는 모델입니다.
    회사, 정부 기관 등 다양한 유형의 조직을 나타내며, 여러 스마트팜 유닛을 소유할 수 있습니다.
    """
    __tablename__ = "organizations"

    # 1. PK를 BigInteger로 설정하여 시스템 전역의 타입 일관성 유지
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True) # 조직의 고유 ID
    
    # --- 주요 조직 정보 ---
    company_name: Mapped[str] = mapped_column(String(255), nullable=False) # 공식 회사명
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False) # 법적 이름
    business_registration_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # 사업자 번호
    
    # --- 담당자 및 연락처 ---
    main_contact_person: Mapped[str] = mapped_column(String(255), nullable=False) # 주요 연락 담당자
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False) # 대표 이메일
    contact_phone: Mapped[str] = mapped_column(String(50), nullable=False) # 대표 전화번호
    address: Mapped[str] = mapped_column(String(255), nullable=False) # 주소
    
    # --- 상태 및 설정 ---
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # 활성화 여부
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1")) # 정보 버전
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # 시간대 (예: 'Asia/Seoul')
    country: Mapped[str] = mapped_column(String(100), nullable=False) # 국가
    currency: Mapped[Optional[str]] = mapped_column(Enum('KRW', 'USD', name='currency_type', create_type=False), nullable=True) # 기본 통화
    
    # --- 산업 및 결제 관련 ---
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # 산업 분야 (예: '농업')
    pg_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # 결제 게이트웨이 ID
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True) # 상세 설명

    # --- 관계 정의 (외래 키) ---
    # organization_type_id는 OrganizationTypeFKMixin으로부터 상속받습니다.

    # --- Relationships ---
    # 2. 신규 추가: 이 조직이 소유한 스마트팜 클러스터(SystemUnit) 목록
    system_units = relationship("SystemUnit", back_populates="organization")
    
    # 기존 관계 유지
    roles = relationship("Role", back_populates="organization") 
    user_roles = relationship("UserOrganizationRole", back_populates="organization")
    organization_devices = relationship("OrganizationDevice", back_populates="organization")
    organization_type = relationship("OrganizationType", back_populates="organizations")
    subscriptions = relationship("OrganizationSubscription", back_populates="organization")