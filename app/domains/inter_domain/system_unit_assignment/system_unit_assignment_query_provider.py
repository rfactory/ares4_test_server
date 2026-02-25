from typing import Optional
from sqlalchemy.orm import Session

from app.models.relationships.system_unit_assignment import SystemUnitAssignment
from app.domains.services.system_unit_assignment.services.system_unit_assignment_query_service import system_unit_assignment_query_service

class SystemUnitAssignmentQueryProvider:
    def is_user_assigned_to_unit(self, db: Session, *, user_id: int, unit_id: int) -> bool:
        return system_unit_assignment_query_service.is_user_assigned_to_unit(
            db, user_id=user_id, unit_id=unit_id
        )
    
    def get_active_owner_assignment(self, db: Session, *, unit_id: int, user_id: int) -> Optional[SystemUnitAssignment]:
        """현재 활성화된(unassigned_at IS NULL) OWNER 할당 정보를 반환합니다."""
        return system_unit_assignment_query_service.get_active_owner_by_unit(
            db, unit_id=unit_id, user_id=user_id
        )
    
    def get_assignment_period(self, db: Session, *, unit_id: int, user_id: int) -> Optional[SystemUnitAssignment]:
        """[도메인 협력용] 특정 유저의 소유 기간 정보를 제공합니다."""
        return system_unit_assignment_query_service.get_assignment_period(db, unit_id=unit_id, user_id=user_id)
    
system_unit_assignment_query_provider = SystemUnitAssignmentQueryProvider()