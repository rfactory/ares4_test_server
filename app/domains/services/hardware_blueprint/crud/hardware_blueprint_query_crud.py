from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.objects.hardware_blueprint import HardwareBlueprint
from app.models.relationships.blueprint_valid_pin import BlueprintValidPin
from ..schemas.hardware_blueprint_query import HardwareBlueprintQuery

class CRUDHardwareBlueprintQuery:
    def get(self, db: Session, *, id: int) -> Optional[HardwareBlueprint]:
        """ID로 하드웨어 블루프린트를 조회합니다."""
        return db.query(HardwareBlueprint).filter(HardwareBlueprint.id == id).first()

    def get_by_version_and_name(
        self, db: Session, *, blueprint_version: str, blueprint_name: str
    ) -> Optional[HardwareBlueprint]:
        """버전과 이름으로 하드웨어 블루프린트를 조회합니다."""
        return db.query(HardwareBlueprint).filter(
            HardwareBlueprint.blueprint_version == blueprint_version,
            HardwareBlueprint.blueprint_name == blueprint_name
        ).first()

    def get_multi(
        self, db: Session, *, query_params: HardwareBlueprintQuery
    ) -> List[HardwareBlueprint]:
        """쿼리 파라미터에 따라 여러 하드웨어 블루프린트를 조회합니다."""
        query = db.query(HardwareBlueprint)

        if query_params.id:
            query = query.filter(HardwareBlueprint.id == query_params.id)
        if query_params.blueprint_version:
            query = query.filter(HardwareBlueprint.blueprint_version == query_params.blueprint_version)
        if query_params.blueprint_name:
            query = query.filter(HardwareBlueprint.blueprint_name == query_params.blueprint_name)
        if query_params.product_line_id:
            query = query.filter(HardwareBlueprint.product_line_id == query_params.product_line_id)
        
        return query.offset(query_params.skip).limit(query_params.limit).all()

    def is_component_valid_for_blueprint(self, db: Session, *, blueprint_id: int, supported_component_id: int) -> bool:
        """
        특정 블루프린트에 대해 특정 부품(supported_component)이 유효한지 확인합니다.
        """
        return db.query(BlueprintValidPin).filter(
            BlueprintValidPin.blueprint_id == blueprint_id,
            BlueprintValidPin.supported_component_id == supported_component_id
        ).first() is not None

hardware_blueprint_crud_query = CRUDHardwareBlueprintQuery()
