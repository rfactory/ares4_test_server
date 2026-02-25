from typing import Optional
from sqlalchemy.orm import Session
from app.models.relationships.system_unit_assignment import SystemUnitAssignment
from ..crud.system_unit_assignment_query_crud import system_unit_assignment_query_crud

class SystemUnitAssignmentQueryService:
    def is_user_assigned_to_unit(self, db: Session, *, user_id: int, unit_id: int) -> bool:
        """사용자가 유닛과 연결되어 있는지 여부를 확인합니다."""
        assignment = system_unit_assignment_query_crud.get_assignment(
            db, user_id=user_id, unit_id=unit_id
        )
        return assignment is not None
    
    def get_active_owner_by_unit(self, db: Session, *, unit_id: int, user_id: int) -> Optional[SystemUnitAssignment]:
        """활성 상태인 OWNER 할당 정보를 조회합니다."""
        # CRUD를 통해 role='OWNER' 및 unassigned_at IS NULL 조건으로 검색
        return system_unit_assignment_query_crud.get_active_assignment(
            db, unit_id=unit_id, user_id=user_id, role="OWNER"
        )
        
    def get_assignment_period(self, db: Session, *, unit_id: int, user_id: int) -> Optional[SystemUnitAssignment]:
        """사용자의 특정 유닛 소유 기간(created_at ~ unassigned_at)을 조회합니다."""
        # CRUD의 get_assignment는 이미 최신순 정렬이 되어 있으므로 그대로 활용하거나,
        # 특정 유저의 '종료된 기록'까지 포함한 가장 최근 기록을 반환합니다.
        return system_unit_assignment_query_crud.get_assignment(db, user_id=user_id, unit_id=unit_id)

system_unit_assignment_query_service = SystemUnitAssignmentQueryService()