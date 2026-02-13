from sqlalchemy.orm import Session
from typing import Optional
from app.models.relationships.system_unit_assignment import AssignmentRoleEnum
from app.domains.services.system_unit_assignment.crud.system_unit_assignment_command_crud import system_unit_assignment_command_crud

class SystemUnitAssignmentCommandService:
    """
    [Command Service] 시스템 유닛의 소유권 및 권한 할당을 전담하는 서비스입니다.
    다른 서비스나 도메인을 호출하지 않으며, 오직 CRUD를 통해 자기 도메인의 상태만 변경합니다.
    """

    def assign_owner(
        self, 
        db: Session, 
        system_unit_id: int, 
        user_id: Optional[int] = None, 
        organization_id: Optional[int] = None
    ):
        """
        시스템 유닛의 소유자(OWNER)를 지정합니다.
        기존 소유자가 있다면 제거하고(Clean Slate) 새로 할당합니다.
        """
        # 1. 기존 소유자 제거 (CRUD 호출)
        system_unit_assignment_command_crud.delete_owner_assignment(db, system_unit_id)
        
        # 2. 새 소유자 할당 (CRUD 호출)
        return system_unit_assignment_command_crud.create_assignment(
            db=db,
            system_unit_id=system_unit_id,
            role=AssignmentRoleEnum.OWNER,
            user_id=user_id,
            organization_id=organization_id
        )

# 싱글톤 인스턴스
system_unit_assignment_command_service = SystemUnitAssignmentCommandService()