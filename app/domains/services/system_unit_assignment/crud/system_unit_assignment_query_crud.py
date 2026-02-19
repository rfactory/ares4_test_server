from sqlalchemy.orm import Session
from app.models.relationships.system_unit_assignment import SystemUnitAssignment

class SystemUnitAssignmentQueryCRUD:
    def get_assignment(self, db: Session, *, user_id: int, unit_id: int) -> SystemUnitAssignment:
        """사용자와 유닛 사이의 현재 소유권 기록을 찾습니다."""
        return db.query(SystemUnitAssignment).filter(
            SystemUnitAssignment.user_id == user_id,
            SystemUnitAssignment.system_unit_id == unit_id
        ).first()

system_unit_assignment_query_crud = SystemUnitAssignmentQueryCRUD()