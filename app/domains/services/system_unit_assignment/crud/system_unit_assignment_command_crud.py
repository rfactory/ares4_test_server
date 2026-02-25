from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
from app.models.relationships.system_unit_assignment import SystemUnitAssignment, AssignmentRoleEnum
from app.core.exceptions import ValidationError

class SystemUnitAssignmentCommandCRUD:
    def create_assignment(
        self, 
        db: Session, 
        system_unit_id: int, 
        role: AssignmentRoleEnum,
        user_id: Optional[int] = None, 
        organization_id: Optional[int] = None
    ) -> SystemUnitAssignment:
        """
        시스템 유닛에 대한 권한(OWNER, OPERATOR 등)을 부여합니다.
        DB의 XOR 제약조건에 따라 user_id와 organization_id 중 하나만 입력해야 합니다.
        """
        if (user_id and organization_id) or (not user_id and not organization_id):
            raise ValidationError("Assignment must target either a User OR an Organization exclusively.")

        assignment = SystemUnitAssignment(
            system_unit_id=system_unit_id,
            user_id=user_id,
            organization_id=organization_id,
            role=role
        )
        db.add(assignment)
        db.flush() # ID 생성을 위해 flush
        return assignment

    def terminate_owner_assignment(self, db: Session, system_unit_id: int) -> int:
        """
        [Scenario A] 해당 유닛의 활성 소유자(OWNER)의 관계를 종료합니다 (Soft Unbind).
        물리적으로 삭제하지 않고 unassigned_at을 마킹하여 이력을 보존합니다.
        """
        from datetime import datetime
        
        # 1. 현재 활성화된(unassigned_at IS NULL) 소유자 레코드를 찾습니다.
        owner_assignment = db.query(SystemUnitAssignment).filter(
            SystemUnitAssignment.system_unit_id == system_unit_id,
            SystemUnitAssignment.role == AssignmentRoleEnum.OWNER,
            SystemUnitAssignment.unassigned_at.is_(None)
        ).first()

        if not owner_assignment:
            return 0

        # 2. 삭제 대신 종료 시점을 기록합니다.
        # 이 업데이트는 models/relationships/system_unit_assignment.py에 정의된 
        # 'close_sub_assignments' 리스너를 트리거하여 운영자/조회자 권한도 연쇄 종료시킵니다.
        owner_assignment.unassigned_at = datetime.now()
        db.flush()
        
        return 1
    
    def update_unassigned_at(self, db: Session, *, assignment_id: int, unassigned_at: datetime):
        """DB 레코드의 unassigned_at 컬럼을 수정합니다 (Soft Unbind)."""
        db.query(SystemUnitAssignment).filter(
            SystemUnitAssignment.id == assignment_id
        ).update({"unassigned_at": unassigned_at})
        
        # update() 호출 후에는 별도의 commit 없이 flush 정도로 상태를 유지하거나 
        # service/policy에서 최종 commit 하도록 둡니다.
        db.flush() 
        return True

# 싱글톤 인스턴스
system_unit_assignment_command_crud = SystemUnitAssignmentCommandCRUD()