from sqlalchemy.orm import Session
from typing import Optional
from app.models.objects.system_unit import SystemUnit
from ..schemas.system_unit_command import SystemUnitUpdate

class SystemUnitCommandCRUD:
    """
    [Pure Command CRUD] system_units 테이블의 상태를 물리적으로 변경합니다.
    """
    def update(self, db: Session, *, unit_id: int, obj_in: SystemUnitUpdate) -> Optional[SystemUnit]:
        db_obj = db.query(SystemUnit).filter(SystemUnit.id == unit_id).first()
        if db_obj:
            # 스키마에서 값이 들어온 필드만 동적으로 업데이트
            update_data = obj_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            
            db.add(db_obj)
            db.flush()  # Policy의 commit을 기다림
        return db_obj

system_unit_command_crud = SystemUnitCommandCRUD()