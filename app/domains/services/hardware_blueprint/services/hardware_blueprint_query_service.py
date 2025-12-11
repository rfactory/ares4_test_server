from sqlalchemy.orm import Session
from typing import List, Optional

from ..crud.hardware_blueprint_query_crud import hardware_blueprint_crud_query
from ..schemas.hardware_blueprint_query import HardwareBlueprintQuery, HardwareBlueprintRead

class HardwareBlueprintQueryService:
    def get_blueprint_by_id(self, db: Session, *, id: int) -> Optional[HardwareBlueprintRead]:
        """ID로 하드웨어 블루프린트를 조회합니다."""
        db_obj = hardware_blueprint_crud_query.get(db, id=id)
        return HardwareBlueprintRead.model_validate(db_obj) if db_obj else None

    def get_blueprint_by_version_and_name(
        self, db: Session, *, blueprint_version: str, blueprint_name: str
    ) -> Optional[HardwareBlueprintRead]:
        """버전과 이름으로 하드웨어 블루프린트를 조회합니다."""
        db_obj = hardware_blueprint_crud_query.get_by_version_and_name(db, blueprint_version=blueprint_version, blueprint_name=blueprint_name)
        return HardwareBlueprintRead.model_validate(db_obj) if db_obj else None

    def get_multiple_blueprints(
        self, db: Session, *, query_params: HardwareBlueprintQuery
    ) -> List[HardwareBlueprintRead]:
        """쿼리 파라미터에 따라 여러 하드웨어 블루프린트를 조회합니다."""
        db_objs = hardware_blueprint_crud_query.get_multi(db, query_params=query_params)
        return [HardwareBlueprintRead.model_validate(obj) for obj in db_objs]

    def get_valid_component_ids_for_blueprint(self, db: Session, *, blueprint_id: int) -> List[int]:
        """
        특정 블루프린트에 대해 유효한 부품(supported_component) ID 목록을 조회합니다.
        """
        return hardware_blueprint_crud_query.get_valid_component_ids_for_blueprint(db, blueprint_id=blueprint_id)

    def is_component_valid_for_blueprint(self, db: Session, *, blueprint_id: int, supported_component_id: int) -> bool:
        """
        특정 블루프린트에 대해 특정 부품이 유효한지 확인합니다.
        """
        return hardware_blueprint_crud_query.is_component_valid_for_blueprint(db, blueprint_id=blueprint_id, supported_component_id=supported_component_id)

hardware_blueprint_query_service = HardwareBlueprintQueryService()
