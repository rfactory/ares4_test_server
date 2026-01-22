from typing import List, Optional
from sqlalchemy.orm import Session

from app.domains.services.organizations.schemas.organization_query import OrganizationResponse, OrganizationTypeResponse
from app.domains.services.organizations.services.organization_query_service import organization_query_service

class OrganizationQueryProvider:
    """
    Organization Query 서비스에 대한 공개 인터페이스입니다。
    """
    def get_organization_by_id(self, db: Session, org_id: int) -> Optional[OrganizationResponse]:
        return organization_query_service.get_organization_by_id(db, org_id=org_id)

    def get_organizations(self, db: Session, skip: int = 0, limit: int = 100) -> List[OrganizationResponse]:
        return organization_query_service.get_organizations(db, skip=skip, limit=limit)

    def search_organizations(self, db: Session, *, search_term: str) -> List[OrganizationResponse]:
        """검색어(이름 또는 사업자 등록 번호)로 조직 목록을 조회합니다."""
        return organization_query_service.search_organizations(db, search_term=search_term)

    def get_organization_by_registration_number(self, db: Session, *, registration_number: str) -> Optional[OrganizationResponse]:
        return organization_query_service.get_organization_by_registration_number(db, registration_number=registration_number)

    def find_organization_by_identifier(self, db: Session, *, identifier: str) -> Optional[OrganizationResponse]:
        """이름 또는 사업자 번호로 조직을 검색합니다."""
        return organization_query_service.find_organization_by_identifier(db, identifier=identifier)

    def get_organization_type_by_id(self, db: Session, *, id: int) -> Optional[OrganizationTypeResponse]:
        return organization_query_service.get_organization_type(db, id=id)

    def get_organization_types(self, db: Session, skip: int = 0, limit: int = 100) -> List[OrganizationTypeResponse]:
        return organization_query_service.get_organization_types(db, skip=skip, limit=limit)

organization_query_provider = OrganizationQueryProvider()
