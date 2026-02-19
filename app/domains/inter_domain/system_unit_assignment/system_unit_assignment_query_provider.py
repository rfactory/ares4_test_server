from sqlalchemy.orm import Session
from app.domains.services.system_unit_assignment.services.system_unit_assignment_query_service import system_unit_assignment_query_service

class SystemUnitAssignmentQueryProvider:
    def is_user_assigned_to_unit(self, db: Session, *, user_id: int, unit_id: int) -> bool:
        return system_unit_assignment_query_service.is_user_assigned_to_unit(
            db, user_id=user_id, unit_id=unit_id
        )

system_unit_assignment_query_provider = SystemUnitAssignmentQueryProvider()