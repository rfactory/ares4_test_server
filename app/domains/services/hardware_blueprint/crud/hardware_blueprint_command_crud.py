from sqlalchemy.orm import Session
from typing import Optional

from app.core.crud_base import CRUDBase
from app.models.objects.hardware_blueprint import HardwareBlueprint
from ..schemas.hardware_blueprint_command import HardwareBlueprintCreate, HardwareBlueprintUpdate

class CRUDHardwareBlueprintCommand(CRUDBase[HardwareBlueprint, HardwareBlueprintCreate, HardwareBlueprintUpdate]):
    def get_by_version_and_name(
        self, db: Session, *, blueprint_version: str, blueprint_name: str
    ) -> Optional[HardwareBlueprint]:
        """버전과 이름으로 하드웨어 블루프린트를 조회합니다."""
        return db.query(self.model).filter(
            self.model.blueprint_version == blueprint_version,
            self.model.blueprint_name == blueprint_name
        ).first()

hardware_blueprint_crud_command = CRUDHardwareBlueprintCommand(HardwareBlueprint)
