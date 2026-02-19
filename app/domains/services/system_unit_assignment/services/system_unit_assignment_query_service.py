from sqlalchemy.orm import Session
from ..crud.system_unit_assignment_query_crud import system_unit_assignment_query_crud

class SystemUnitAssignmentQueryService:
    def is_user_assigned_to_unit(self, db: Session, *, user_id: int, unit_id: int) -> bool:
        """사용자가 유닛의 주인인지 여부를 확인합니다."""
        assignment = system_unit_assignment_query_crud.get_assignment(
            db, user_id=user_id, unit_id=unit_id
        )
        return assignment is not None

system_unit_assignment_query_service = SystemUnitAssignmentQueryService()