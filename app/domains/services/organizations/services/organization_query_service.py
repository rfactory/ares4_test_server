# C:\vscode project files\Ares4\server2\app\domains\services\organizations\services\organization_query_service.py
from typing import List, Optional

from sqlalchemy.orm import Session

from ..crud.organization_query_crud import organization_crud_query
from ..schemas.organization_query import OrganizationResponse

class OrganizationQueryService:
    """
    조직(Organization) 정보에 대한 조회 'Query' 성격의 비즈니스 로직을 담당합니다.
    """
    def get_organization(self, db: Session, org_id: int) -> Optional[OrganizationResponse]:
        """ID로 특정 조직 정보를 조회합니다."""
        db_obj = organization_crud_query.get(db, id=org_id)
        return OrganizationResponse.model_validate(db_obj) if db_obj else None

    def get_organizations(self, db: Session, skip: int = 0, limit: int = 100) -> List[OrganizationResponse]:
        """여러 조직 정보를 페이지네이션하여 조회합니다."""
        db_objs = organization_crud_query.get_multi(db, skip=skip, limit=limit)
        return [OrganizationResponse.model_validate(obj) for obj in db_objs]

    def get_organization_by_registration_number(self, db: Session, *, registration_number: str) -> Optional[OrganizationResponse]:
        """사업자 등록 번호로 특정 조직 정보를 조회합니다."""
        db_obj = organization_crud_query.get_by_registration_number(db, registration_number=registration_number)
        return OrganizationResponse.model_validate(db_obj) if db_obj else None

organization_query_service = OrganizationQueryService()
