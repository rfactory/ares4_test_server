from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.objects.role import Role
from app.models.relationships.user_organization_role import UserOrganizationRole

class CRUDGovernanceQuery:
    def get_role_by_name(self, db: Session, *, name: str, scope: str) -> Role | None:
        """이름과 범위로 역할을 조회합니다."""
        return db.query(Role).filter(Role.name == name, Role.scope == scope).first()

    def get_user_count_by_role_id(self, db: Session, *, role_id: int) -> int:
        """특정 역할에 할당된 사용자 수를 조회합니다."""
        return db.query(func.count(UserOrganizationRole.user_id)).filter(UserOrganizationRole.role_id == role_id).scalar() or 0

governance_query_crud = CRUDGovernanceQuery()
