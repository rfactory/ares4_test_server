# C:\vscode project files\Ares4\server2\app\domains\services\organizations\schemas\organization_query.py
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

# --- Query-related Schemas ---
# 이 파일은 데이터의 상태를 변경하지 않는 'Query' 작업과 관련된 Pydantic 스키마들을 정의합니다.
# (조회)

class OrganizationTypeBase(BaseModel):
    """조직 유형의 기본 필드를 정의하는 스키마입니다."""
    # 조직 유형의 이름 (예: 일반, 파트너)
    name: str
    # 조직 유형에 대한 설명
    description: Optional[str] = None

class OrganizationTypeResponse(OrganizationTypeBase):
    """
    API 응답으로 사용될 조직 유형 스키마입니다.
    읽기 전용 필드인 'id'를 포함합니다.
    """
    # 조직 유형의 고유 ID
    id: int

    model_config = {
        "from_attributes": True, # SQLAlchemy ORM 객체로부터 자동 매핑 활성화
    }

class OrganizationResponse(BaseModel):
    """
    API 응답으로 사용될 조직 정보 스키마입니다.
    데이터베이스에서 조회된 조직 정보를 클라이언트에게 반환할 때 사용됩니다.
    'created_at', 'version' 등과 같은 읽기 전용 필드 및 중첩된 관계(organization_type)를 포함합니다.
    """
    # 조직의 고유 ID
    id: int
    # 회사의 공식 명칭
    company_name: Optional[str] = None
    # 본사 주소
    address: Optional[str] = None
    # 주요 연락 이메일
    contact_email: Optional[str] = None
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
    # 레코드 생성 시각
    created_at: datetime
    # 레코드 마지막 수정 시각
    updated_at: datetime
    # 레코드 버전 (낙관적 잠금용)
    version: int
    # 조직 유형 정보 (중첩된 관계)
    organization_type: OrganizationTypeResponse

    model_config = {
        "from_attributes": True, # SQLAlchemy ORM 객체로부터 자동 매핑 활성화
    }
