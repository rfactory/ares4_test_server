from sqlalchemy.orm import Session

from app.domains.services.hardware_blueprint.schemas.hardware_blueprint_command import HardwareBlueprintCreate, HardwareBlueprintUpdate
from app.domains.services.hardware_blueprint.services.hardware_blueprint_command_service import hardware_blueprint_command_service
from app.models.objects.hardware_blueprint import HardwareBlueprint as DBHardwareBlueprint
from app.models.objects.user import User

class HardwareBlueprintCommandProvider:
    """
    [Inter-Domain Provider]
    외부 도메인(Policy 등)에서 하드웨어 블루프린트 상태 변경을 요청하는 인터페이스입니다.
    Pure Command 원칙에 따라, 수정/삭제 시에는 조회된 객체를 직접 전달받습니다.
    """

    def create_blueprint(
        self, db: Session, *, obj_in: HardwareBlueprintCreate, actor_user: User
    ) -> DBHardwareBlueprint:
        """새로운 하드웨어 블루프린트를 생성합니다."""
        return hardware_blueprint_command_service.create_blueprint(
            db, 
            obj_in=obj_in, 
            actor_user=actor_user
        )

    def update_blueprint(
        self, db: Session, *, db_obj: DBHardwareBlueprint, obj_in: HardwareBlueprintUpdate, actor_user: User
    ) -> DBHardwareBlueprint:
        """기존 하드웨어 블루프린트를 업데이트합니다."""
        return hardware_blueprint_command_service.update_blueprint(
            db, 
            db_obj=db_obj, 
            obj_in=obj_in, 
            actor_user=actor_user
        )

    def delete_blueprint(self, db: Session, *, db_obj: DBHardwareBlueprint, actor_user: User) -> DBHardwareBlueprint:
        """하드웨어 블루프린트를 삭제합니다."""
        return hardware_blueprint_command_service.delete_blueprint(
            db, 
            db_obj=db_obj, 
            actor_user=actor_user
        )

hardware_blueprint_command_provider = HardwareBlueprintCommandProvider()