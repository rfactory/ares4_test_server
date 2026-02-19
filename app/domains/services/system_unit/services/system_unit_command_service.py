from sqlalchemy.orm import Session
from typing import Optional
from ..crud.system_unit_command_crud import system_unit_command_crud
from ..schemas.system_unit_command import SystemUnitUpdate
from app.models.objects.user import User

class SystemUnitCommandService:
    def update_unit_status(
        self, 
        db: Session, 
        *, 
        unit_id: int, 
        status: str, 
        actor_user: Optional[User] = None
    ):
        # 원시 값들을 스키마 객체로 포장하여 CRUD에 전달
        obj_in = SystemUnitUpdate(status=status)
        
        db_obj = system_unit_command_crud.update(db, unit_id=unit_id, obj_in=obj_in)
        
        if db_obj and actor_user:
            from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
            audit_command_provider.log_event(
                db=db,
                actor_user=actor_user,
                event_type="UNIT_STATUS_UPDATED",
                description=f"System Unit {unit_id} status changed to {status}",
                details={"unit_id": unit_id, "new_status": status}
            )
        return db_obj

system_unit_command_service = SystemUnitCommandService()