from typing import List, Optional

from sqlalchemy.orm import Session

from ..crud.organization_query_crud import organization_crud_query
from ..crud.organization_type_query_crud import organization_type_crud_query
from ..schemas.organization_query import OrganizationResponse, OrganizationTypeResponse

class OrganizationQueryService:
    """
    조직(Organization) 정보 및 관련 객체에 대한 조회 'Query' 성격의 비즈니스 로직을 담당합니다.
    """
    def get_organization_by_id(self, db: Session, org_id: int) -> Optional[OrganizationResponse]:
        """ID로 특정 조직 정보를 조회합니다."""
        db_obj = organization_crud_query.get(db, id=org_id)
        return OrganizationResponse.model_validate(db_obj) if db_obj else None

    def get_organizations(self, db: Session, skip: int = 0, limit: int = 100) -> List[OrganizationResponse]:
        """여러 조직 정보를 페이지네이션하여 조회합니다."""
        db_objs = organization_crud_query.get_multi(db, skip=skip, limit=limit)
        return [OrganizationResponse.model_validate(obj) for obj in db_objs]

    def search_organizations(self, db: Session, *, search_term: str) -> List[OrganizationResponse]:
        """검색어(이름 또는 사업자 등록 번호)로 조직 목록을 조회합니다."""
        db_objs = organization_crud_query.search_organizations(db, search_term=search_term)
        return [OrganizationResponse.model_validate(obj) for obj in db_objs]

    def get_organization_by_registration_number(self, db: Session, *, registration_number: str) -> Optional[OrganizationResponse]:
        """사업자 등록 번호로 특정 조직 정보를 조회합니다."""
        db_obj = organization_crud_query.get_by_registration_number(db, registration_number=registration_number)
        return OrganizationResponse.model_validate(db_obj) if db_obj else None

    def find_organization_by_identifier(self, db: Session, *, identifier: str) -> Optional[OrganizationResponse]:
        """이름 또는 사업자 번호로 조직을 검색합니다."""
        db_obj = organization_crud_query.find_by_identifier(db, identifier=identifier)
        return OrganizationResponse.model_validate(db_obj) if db_obj else None

    def get_organization_type(self, db: Session, *, id: int) -> Optional[OrganizationTypeResponse]:
        """ID를 기준으로 특정 조직 유형 정보를 조회합니다."""
        db_obj = organization_type_crud_query.get(db, id=id)
        return OrganizationTypeResponse.model_validate(db_obj) if db_obj else None

    def get_organization_types(self, db: Session, skip: int = 0, limit: int = 100) -> List[OrganizationTypeResponse]:
        """여러 조직 유형 정보를 페이지네이션하여 조회합니다."""
        db_objs = organization_type_crud_query.get_multi(db, skip=skip, limit=limit)
        return [OrganizationTypeResponse.model_validate(obj) for obj in db_objs]

organization_query_service = OrganizationQueryService()
