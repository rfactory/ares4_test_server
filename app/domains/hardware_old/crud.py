from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.hardware_blueprint import HardwareBlueprint
from app.models.relationships.blueprint_pin_mapping import BlueprintPinMapping

class CRUDHardwareBlueprint:
    def get(self, db: Session, blueprint_id: int) -> Optional[HardwareBlueprint]:
        return db.query(HardwareBlueprint).filter(HardwareBlueprint.id == blueprint_id).first()

    def is_component_valid_for_blueprint(
        self, db: Session, blueprint_id: int, supported_component_id: int
    ) -> bool:
        """
        Checks if a supported component is valid for a given hardware blueprint.
        This is determined by the existence of a BlueprintPinMapping.
        """
        return db.query(BlueprintPinMapping).filter(
            BlueprintPinMapping.hardware_blueprint_id == blueprint_id,
            BlueprintPinMapping.supported_component_id == supported_component_id
        ).first() is not None

hardware_blueprint_crud = CRUDHardwareBlueprint()
