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

# 싱글톤 인스턴스
system_unit_assignment_command_provider = SystemUnitAssignmentCommandProvider()