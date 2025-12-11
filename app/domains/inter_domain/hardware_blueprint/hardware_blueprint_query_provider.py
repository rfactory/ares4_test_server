# app/domains/inter_domain/hardware_blueprint/hardware_blueprint_query_provider.py
from sqlalchemy.orm import Session
from typing import List, Optional

from app.domains.services.hardware_blueprint.schemas.hardware_blueprint_query import HardwareBlueprintQuery, HardwareBlueprintRead
from app.domains.services.hardware_blueprint.services.hardware_blueprint_query_service import hardware_blueprint_query_service

class HardwareBlueprintQueryProvider:
    def get_blueprint_by_id(self, db: Session, *, id: int) -> Optional[HardwareBlueprintRead]:
        """ID로 하드웨어 블루프린트를 조회합니다."""
        return hardware_blueprint_query_service.get_blueprint_by_id(db, id=id)

    def get_blueprint_by_version_and_name(
        self, db: Session, *, blueprint_version: str, blueprint_name: str
    ) -> Optional[HardwareBlueprintRead]:
        """버전과 이름으로 하드웨어 블루프린트를 조회합니다."""
        return hardware_blueprint_query_service.get_blueprint_by_version_and_name(
            db, blueprint_version=blueprint_version, blueprint_name=blueprint_name
        )

    def get_multiple_blueprints(
        self, db: Session, *, query_params: HardwareBlueprintQuery
    ) -> List[HardwareBlueprintRead]:
        """쿼리 파라미터에 따라 여러 하드웨어 블루프린트를 조회합니다."""
        return hardware_blueprint_query_service.get_multiple_blueprints(db, query_params=query_params)

    def get_valid_component_ids_for_blueprint(self, db: Session, *, blueprint_id: int) -> List[int]:
        """
        특정 블루프린트에 대해 유효한 부품(supported_component) ID 목록을 조회합니다.
        """
        return hardware_blueprint_query_service.get_valid_component_ids_for_blueprint(db, blueprint_id=blueprint_id)

    def is_component_valid_for_blueprint(self, db: Session, *, blueprint_id: int, supported_component_id: int) -> bool:
        """
        특정 블루프린트에 대해 특정 부품이 유효한지 확인합니다.
        """
        return hardware_blueprint_query_service.is_component_valid_for_blueprint(db, blueprint_id=blueprint_id, supported_component_id=supported_component_id)

hardware_blueprint_query_provider = HardwareBlueprintQueryProvider()

