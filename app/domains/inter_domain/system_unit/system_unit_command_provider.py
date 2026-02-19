from sqlalchemy.orm import Session
from typing import Optional
from app.domains.services.system_unit.services.system_unit_command_service import system_unit_command_service
from app.models.objects.user import User

class SystemUnitCommandProvider:
    """
    [Inter-Domain Provider] 
    Policy나 다른 도메인에서 시스템 유닛의 상태를 변경하고자 할 때 부르는 통로입니다.
    """
    def update_unit_status(
        self, 
        db: Session, 
        *, 
        unit_id: int, 
        status: str, 
        actor_user: Optional[User] = None
    ):
        return system_unit_command_service.update_unit_status(
            db, unit_id=unit_id, status=status, actor_user=actor_user
        )

system_unit_command_provider = SystemUnitCommandProvider()