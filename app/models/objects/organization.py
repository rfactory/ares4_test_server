# app/models/objects/organization.py
from sqlalchemy import Column, Integer, String, Boolean, Enum, text
from sqlalchemy.orm import relationship, Mapped, mapped_column # Added Mapped, mapped_column
from typing import Optional # Added Optional

from app.database import Base
from ..base_model import TimestampMixin, OrganizationTypeFKMixin # OrganizationTypeFKMixin 추가
class Organization(Base, TimestampMixin, OrganizationTypeFKMixin): # OrganizationTypeFKMixin 상속
    """
    조직 정보를 저장하는 모델입니다.
    회사, 정부 기관 등 다양한 유형의 조직을 나타냅니다.
    """
    __tablename__ = "organizations"
    # --- 사용자 템플릿 순서에 맞는 컬럼들 ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) # 조직의 고유 ID
    company_name: Mapped[str] = mapped_column(String(255), nullable=False) # 조직의 공식 회사명
    address: Mapped[str] = mapped_column(String(255), nullable=False) # 조직의 주소
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False) # 조직의 대표 연락 이메일
    business_registration_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # 사업자 등록 번호 또는 고유 식별 번호
    contact_phone: Mapped[str] = mapped_column(String(50), nullable=False) # 조직의 대표 연락 전화번호
    website_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # 조직의 웹사이트 URL
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # 조직 계정의 활성화 여부
    main_contact_person: Mapped[str] = mapped_column(String(255), nullable=False) # 조직의 주요 연락 담당자 이름
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1")) # 조직 정보의 버전 (낙관적 잠금 등에 사용)
    # --- 사용자 템플릿에 없어서 아래로 이동한 컬럼들 ---
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # 조직의 기본 시간대 (예: 'Asia/Seoul')
    country: Mapped[str] = mapped_column(String(100), nullable=False) # 조직이 위치한 국가
    currency: Mapped[Optional[str]] = mapped_column(Enum('KRW', 'USD', name='currency_type', create_type=False), nullable=True) # 조직의 기본 통화 (예: 'KRW', 'USD')
    pg_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # 결제 게이트웨이 고객 ID
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False) # 조직의 법적 이름
    representative_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # 조직의 대표자 이름
    business_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # 사업 유형 (예: '제조업', '서비스업')
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # 산업 분야 (예: '농업', 'IT')
    billing_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # 청구서 수신 주소
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # 세금 식별 번호
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True) # 조직에 대한 추가 설명

    # --- 관계 정의 (외래 키) ---
    # organization_type_id는 OrganizationTypeFKMixin으로부터 상속받습니다.

    # --- Relationships ---
    roles = relationship("Role", back_populates="organization") # 이 조직에 정의된 역할 목록
    user_roles = relationship("UserOrganizationRole", back_populates="organization") # 이 조직에 속한 사용자-역할 관계 목록
    organization_devices = relationship("OrganizationDevice", back_populates="organization") # 이 조직에 할당된 장치 정보 (관계 테이블)
    organization_type = relationship("OrganizationType", back_populates="organizations") # 이 조직의 유형 정보
    subscriptions = relationship("OrganizationSubscription", back_populates="organization") # 이 조직의 구독 정보 목록