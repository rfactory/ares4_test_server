# app/domains/inter_domain/hardware_blueprint/hardware_blueprint_command_provider.py
from sqlalchemy.orm import Session

from app.domains.services.hardware_blueprint.schemas.hardware_blueprint_command import HardwareBlueprintCreate, HardwareBlueprintUpdate
from app.domains.services.hardware_blueprint.services.hardware_blueprint_command_service import hardware_blueprint_command_service
from app.models.objects.hardware_blueprint import HardwareBlueprint as DBHardwareBlueprint
from app.models.objects.user import User


class HardwareBlueprintCommandProvider:
    def create_blueprint(
        self, db: Session, *, obj_in: HardwareBlueprintCreate, actor_user: User
    ) -> DBHardwareBlueprint:
        """새로운 하드웨어 블루프린트를 생성합니다."""
        return hardware_blueprint_command_service.create_blueprint(db, obj_in=obj_in, actor_user=actor_user)

    def update_blueprint(
        self, db: Session, *, id: int, obj_in: HardwareBlueprintUpdate, actor_user: User
    ) -> DBHardwareBlueprint:
        """기존 하드웨어 블루프린트를 업데이트합니다."""
        return hardware_blueprint_command_service.update_blueprint(db, id=id, obj_in=obj_in, actor_user=actor_user)

    def delete_blueprint(self, db: Session, *, id: int, actor_user: User) -> DBHardwareBlueprint:
        """하드웨어 블루프린트를 삭제합니다."""
        return hardware_blueprint_command_service.delete_blueprint(db, id=id, actor_user=actor_user)

hardware_blueprint_command_provider = HardwareBlueprintCommandProvider()
