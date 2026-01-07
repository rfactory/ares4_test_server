from sqlalchemy.orm import Session
from app.core.crud_base import CRUDBase
from app.models.objects.organization_type import OrganizationType

class CRUDOrganizationTypeQuery(CRUDBase[OrganizationType, None, None]):
    # OrganizationType은 조회만 필요하므로, Create/Update 스키마는 None으로 지정합니다.
    def get_by_name(self, db: Session, *, name: str) -> OrganizationType | None:
        return db.query(self.model).filter(self.model.name == name).first()

organization_type_crud_query = CRUDOrganizationTypeQuery(model=OrganizationType)
