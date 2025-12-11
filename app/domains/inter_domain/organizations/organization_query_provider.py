# C:\vscode project files\Ares4\server2\app\domains\inter_domain\organization\organization_query_provider.py
from typing import List, Optional
from sqlalchemy.orm import Session

from app.domains.services.organizations.schemas.organization_query import OrganizationResponse
from app.domains.services.organizations.services.organization_query_service import organization_query_service

class OrganizationQueryProvider:
    """
    Organization Query 서비스에 대한 공개 인터페이스입니다.
    외부 도메인은 이 Provider를 통해서만 데이터 조회 기능에 접근해야 합니다.
    """
    def get_organization(self, db: Session, org_id: int) -> Optional[OrganizationResponse]:
        return organization_query_service.get_organization(db, org_id=org_id)

    def get_organizations(self, db: Session, skip: int = 0, limit: int = 100) -> List[OrganizationResponse]:
        return organization_query_service.get_organizations(db, skip=skip, limit=limit)

    def get_organization_by_registration_number(self, db: Session, *, registration_number: str) -> Optional[OrganizationResponse]:
        return organization_query_service.get_organization_by_registration_number(db, registration_number=registration_number)

organization_query_provider = OrganizationQueryProvider()
