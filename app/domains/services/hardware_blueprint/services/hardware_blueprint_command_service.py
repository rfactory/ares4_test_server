from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, DuplicateEntryError
from app.models.objects.hardware_blueprint import HardwareBlueprint as DBHardwareBlueprint
from app.models.objects.product_line import ProductLine
from app.models.objects.user import User
from ..crud.hardware_blueprint_command_crud import hardware_blueprint_crud_command
from ..schemas.hardware_blueprint_command import HardwareBlueprintCreate, HardwareBlueprintUpdate
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

class HardwareBlueprintCommandService:
    def create_blueprint(
        self, db: Session, *, obj_in: HardwareBlueprintCreate, actor_user: User
    ) -> DBHardwareBlueprint:
        """새로운 하드웨어 블루프린트를 생성합니다."""
        
        # [수정] product_line_id가 None이 아닐 때만 유효성 검사를 수행합니다.
        # (기존 코드는 None이면 NotFoundError를 발생시킴)
        if obj_in.product_line_id is not None:
            if not db.query(ProductLine).filter(ProductLine.id == obj_in.product_line_id).first():
                raise NotFoundError("ProductLine", str(obj_in.product_line_id))

        # 방어적 확인 2: 버전과 이름의 조합이 고유한지 확인
        existing = hardware_blueprint_crud_command.get_by_version_and_name(
            db, blueprint_version=obj_in.blueprint_version, blueprint_name=obj_in.blueprint_name
        )
        if existing:
            raise DuplicateEntryError(
                "HardwareBlueprint", 
                "blueprint_version and blueprint_name", 
                f"{obj_in.blueprint_version} - {obj_in.blueprint_name}"
            )

        # [참고] obj_in.specs (Pydantic 모델)는 CRUD 내부의 jsonable_encoder에 의해 
        # 자동으로 dict로 변환되어 JSONB 컬럼에 저장됩니다. 별도 수정 불필요.
        db_obj = hardware_blueprint_crud_command.create(db, obj_in=obj_in)
        db.flush()
        
        audit_command_provider.log_creation(
            db=db,
            actor_user=actor_user,
            resource_name="HardwareBlueprint",
            resource_id=db_obj.id,
            new_value=db_obj.as_dict()
        )
        return db_obj

    def update_blueprint(
        self, db: Session, *, id: int, obj_in: HardwareBlueprintUpdate, actor_user: User
    ) -> DBHardwareBlueprint:
        """기존 하드웨어 블루프린트를 업데이트합니다."""
        db_obj = hardware_blueprint_crud_command.get(db, id=id)
        if not db_obj:
            raise NotFoundError("HardwareBlueprint", str(id))
        
        # [수정] Update 시에도 값이 들어왔을 때만 검증 (Optional 처리)
        if obj_in.product_line_id is not None:
            if not db.query(ProductLine).filter(ProductLine.id == obj_in.product_line_id).first():
                raise NotFoundError("ProductLine", str(obj_in.product_line_id))
            
        old_value = db_obj.as_dict()
        
        updated_obj = hardware_blueprint_crud_command.update(db, db_obj=db_obj, obj_in=obj_in)
        db.flush()
        
        audit_command_provider.log_update(
            db=db,
            actor_user=actor_user,
            resource_name="HardwareBlueprint",
            resource_id=updated_obj.id,
            old_value=old_value,
            new_value=updated_obj.as_dict()
        )
        return updated_obj

    def delete_blueprint(self, db: Session, *, id: int, actor_user: User) -> DBHardwareBlueprint:
        # 삭제 로직은 변경 없음
        db_obj = hardware_blueprint_crud_command.get(db, id=id)
        if not db_obj:
            raise NotFoundError("HardwareBlueprint", str(id))
        
        old_value = db_obj.as_dict()

        deleted_obj = hardware_blueprint_crud_command.remove(db, id=id)
        db.flush()
        
        audit_command_provider.log_deletion(
            db=db,
            actor_user=actor_user,
            resource_name="HardwareBlueprint",
            resource_id=id,
            deleted_value=old_value
        )
        return deleted_obj

hardware_blueprint_command_service = HardwareBlueprintCommandService()