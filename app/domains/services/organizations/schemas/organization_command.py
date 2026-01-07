# C:\vscode project files\Ares4\server2\app\domains\services\organizations\schemas\organization_command.py
from typing import Optional
from pydantic import BaseModel, EmailStr

# --- Command-related Schemas ---
# 이 파일은 데이터의 상태를 변경하는 'Command' 작업과 관련된 Pydantic 스키마들을 정의합니다.
# (생성, 수정, 삭제)

class OrganizationBase(BaseModel):
    """
    조직 데이터의 기본 필드를 정의하는 스키마입니다.
    Create와 Update 스키마의 기반으로 사용되며, 모든 필드가 Optional로 선언되어 유연성을 제공합니다.
    """
    # 회사의 공식 명칭
    company_name: Optional[str] = None
    # 본사 주소
    address: Optional[str] = None
    # 주요 연락 이메일
    contact_email: Optional[EmailStr] = None
    # 사업자 등록 번호
    business_registration_number: Optional[str] = None
    # 주요 연락처
    contact_phone: Optional[str] = None
    # 회사 웹사이트 URL
    website_url: Optional[str] = None
    # 활성화 상태 여부
    is_active: Optional[bool] = True
    # 주요 담당자 이름
    main_contact_person: Optional[str] = None
    # 시간대 (예: Asia/Seoul)
    timezone: Optional[str] = None
    # 국가 코드 (예: KR)
    country: Optional[str] = None
    # 통화 코드 (예: KRW)
    currency: Optional[str] = None
    # PG사(결제 대행사)의 고객 ID
    pg_customer_id: Optional[str] = None
    # 법인명
    legal_name: Optional[str] = None
    # 대표자명
    representative_name: Optional[str] = None
    # 업태
    business_type: Optional[str] = None
    # 업종
    industry: Optional[str] = None
    # 청구서 발송 주소
    billing_address: Optional[str] = None
    # 세금 식별 번호
    tax_id: Optional[str] = None
    # 조직에 대한 추가 설명
    description: Optional[str] = None
    # 조직 유형 ID (외래 키)
    organization_type_id: Optional[int] = None

class OrganizationCreate(OrganizationBase):
    """
    새로운 조직을 생성할 때 사용되는 스키마입니다.
    OrganizationBase를 상속받아, 생성 시 반드시 필요한 필드들을 필수로(Required) 재정의합니다.
    """
    company_name: str
    address: str
    contact_email: EmailStr
    business_registration_number: str
    contact_phone: str
    main_contact_person: str
    country: str
    legal_name: str
    organization_type_id: int

class OrganizationUpdate(OrganizationBase):
    """
    기존 조직의 정보를 수정할 때 사용되는 스키마입니다.
    OrganizationBase를 그대로 상속받아 모든 필드가 Optional이므로, 부분적인 데이터 수정(Partial Update)이 가능합니다.
    """
    pass


# --- Organization Type Schemas ---

class OrganizationTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
