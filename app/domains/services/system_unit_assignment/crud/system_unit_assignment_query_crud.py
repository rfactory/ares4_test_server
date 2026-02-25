from typing import Optional
from sqlalchemy.orm import Session
from app.models.relationships.system_unit_assignment import SystemUnitAssignment

class SystemUnitAssignmentQueryCRUD:
    def get_assignment(self, db: Session, *, user_id: int, unit_id: int) -> Optional[SystemUnitAssignment]:
        """사용자와 유닛 사이의 가장 최근 소유권 기록을 찾습니다."""
        return db.query(SystemUnitAssignment).filter(
            SystemUnitAssignment.user_id == user_id,
            SystemUnitAssignment.system_unit_id == unit_id
        ).order_by(SystemUnitAssignment.created_at.desc()).first()
        
    def get_active_assignment(
        self, db: Session, *, unit_id: int, user_id: int, role: str
    ) -> Optional[SystemUnitAssignment]:
        """
        특정 역할을 가진 '활성화된' 할당 정보를 조회합니다.
        핵심 조건: unassigned_at IS NULL
        """
        return db.query(SystemUnitAssignment).filter(
            SystemUnitAssignment.system_unit_id == unit_id,
            SystemUnitAssignment.user_id == user_id,
            SystemUnitAssignment.role == role,
            SystemUnitAssignment.unassigned_at.is_(None)
        ).first()

system_unit_assignment_query_crud = SystemUnitAssignmentQueryCRUD()