from sqlalchemy.orm import Session

from app.domains.services.governance.crud.governance_query_crud import governance_query_crud

class GovernanceQueryService:
    def get_prime_admin_count(self, db: Session) -> int:
        """Prime_Admin 역할의 현재 사용자 수를 반환합니다."""
        prime_admin_role = governance_query_crud.get_role_by_name(db, name="Prime_Admin", scope="SYSTEM")
        if not prime_admin_role:
            return 0
        return governance_query_crud.get_user_count_by_role_id(db, role_id=prime_admin_role.id)

governance_query_service = GovernanceQueryService()
