from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
from app.domains.services.system_unit_assignment.services.system_unit_assignment_command_service import system_unit_assignment_command_service

class SystemUnitAssignmentCommandProvider:
    """
    [Inter-Domain Provider] 
    시스템 유닛 할당 도메인의 기능을 외부(Policy 등)에서 사용할 수 있도록 제공하는 브릿지입니다.
    """

    def assign_owner(
        self, 
        db: Session, 
        unit_id: int, 
        user_id: Optional[int] = None, 
        organization_id: Optional[int] = None
    ):
        """
        Policy로부터 요청을 받아 유닛의 소유권을 할당하는 서비스로 전달합니다.
        """
        return system_unit_assignment_command_service.assign_owner(
            db=db,
            system_unit_id=unit_id,
            user_id=user_id,
            organization_id=organization_id
        )
    
    def terminate_assignment(self, db: Session, *, assignment_id: int, unassigned_at: datetime):
        """할당 기록을 삭제하지 않고 종료 시점만 기록하도록 서비스에 요청합니다."""
        return system_unit_assignment_command_service.terminate_assignment(
            db=db, assignment_id=assignment_id, unassigned_at=unassigned_at
        )

# 싱글톤 인스턴스
system_unit_assignment_command_provider = SystemUnitAssignmentCommandProvider()