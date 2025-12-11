# C:\vscode project files\Ares4\server2\app\domains\services\organizations\crud\organization_query_crud.py
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.objects.organization import Organization

# --- Query-related CRUD ---
# 이 파일은 데이터의 상태를 변경하지 않고 DB에서 데이터를 조회하는 'Query' CRUD 클래스를 정의합니다.

class CRUDOrganizationQuery:
    """
    조직(Organization) 정보에 대한 조회(Read) DB 작업을 담당합니다.
    """
    def get(self, db: Session, id: int) -> Optional[Organization]:
        """ID를 기준으로 특정 조직 정보를 조회합니다."""
        return db.query(Organization).filter(Organization.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Organization]:
        """여러 조직 정보를 페이지네이션하여 조회합니다."""
        return db.query(Organization).offset(skip).limit(limit).all()

    def get_by_registration_number(self, db: Session, *, registration_number: str) -> Optional[Organization]:
        """사업자 등록 번호를 기준으로 특정 조직 정보를 조회합니다."""
        return db.query(Organization).filter(Organization.business_registration_number == registration_number).first()

organization_crud_query = CRUDOrganizationQuery()
