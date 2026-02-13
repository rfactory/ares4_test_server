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

    def delete_owner_assignment(self, db: Session, system_unit_id: int) -> int:
        """
        해당 유닛의 기존 소유자(OWNER)를 제거합니다.
        (DB 트리거에 의해 하위 권한들도 자동 삭제될 수 있음)
        """
        deleted_count = db.query(SystemUnitAssignment).filter(
            SystemUnitAssignment.system_unit_id == system_unit_id,
            SystemUnitAssignment.role == AssignmentRoleEnum.OWNER
        ).delete()
        db.flush()
        return deleted_count

# 싱글톤 인스턴스
system_unit_assignment_command_crud = SystemUnitAssignmentCommandCRUD()