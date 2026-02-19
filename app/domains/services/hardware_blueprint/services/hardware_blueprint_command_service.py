import logging
from sqlalchemy.orm import Session
from typing import Any

from app.models.objects.hardware_blueprint import HardwareBlueprint as DBHardwareBlueprint
from app.models.objects.user import User
from ..crud.hardware_blueprint_command_crud import hardware_blueprint_crud_command
from ..schemas.hardware_blueprint_command import HardwareBlueprintCreate, HardwareBlueprintUpdate
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class HardwareBlueprintCommandService:
    """
    [Pure Command Service]
    비즈니스 로직(조회/검증)을 배제하고, 오직 DB 상태 변경과 감사 로그 기록만 수행합니다.
    """

    def create_blueprint(
        self, db: Session, *, obj_in: HardwareBlueprintCreate, actor_user: User
    ) -> DBHardwareBlueprint:
        """새로운 하드웨어 블루프린트를 DB에 생성합니다."""
        # 실행: 객체 생성
        db_obj = hardware_blueprint_crud_command.create(db, obj_in=obj_in)
        db.flush()
        
        # 기록: 감사 로그
        audit_command_provider.log_creation(
            db=db,
            actor_user=actor_user,
            resource_name="HardwareBlueprint",
            resource_id=db_obj.id,
            new_value=db_obj.as_dict()
        )
        return db_obj

    def update_blueprint(
        self, db: Session, *, db_obj: DBHardwareBlueprint, obj_in: HardwareBlueprintUpdate, actor_user: User
    ) -> DBHardwareBlueprint:
        """이미 조회된 블루프린트 객체(db_obj)를 업데이트합니다."""
        old_value = db_obj.as_dict()
        
        # 실행: 업데이트
        updated_obj = hardware_blueprint_crud_command.update(db, db_obj=db_obj, obj_in=obj_in)
        db.flush()
        
        # 기록: 감사 로그
        audit_command_provider.log_update(
            db=db,
            actor_user=actor_user,
            resource_name="HardwareBlueprint",
            resource_id=updated_obj.id,
            old_value=old_value,
            new_value=updated_obj.as_dict()
        )
        return updated_obj

    def delete_blueprint(self, db: Session, *, db_obj: DBHardwareBlueprint, actor_user: User) -> DBHardwareBlueprint:
        """이미 조회된 블루프린트 객체(db_obj)를 삭제합니다."""
        old_value = db_obj.as_dict()

        # 실행: 삭제
        deleted_obj = hardware_blueprint_crud_command.remove(db, id=db_obj.id)
        db.flush()
        
        # 기록: 감사 로그
        audit_command_provider.log_deletion(
            db=db,
            actor_user=actor_user,
            resource_name="HardwareBlueprint",
            resource_id=db_obj.id,
            deleted_value=old_value
        )
        return deleted_obj

hardware_blueprint_command_service = HardwareBlueprintCommandService()