# app/domains/inter_domain/hardware_blueprint/hardware_blueprint_query_provider.py
from sqlalchemy.orm import Session
from typing import List, Optional

from app.domains.services.hardware_blueprint.schemas.hardware_blueprint_query import HardwareBlueprintQuery, HardwareBlueprintRead, BlueprintPinMappingRead
from app.domains.services.hardware_blueprint.services.hardware_blueprint_query_service import hardware_blueprint_query_service

class HardwareBlueprintQueryProvider:
    """
    [Inter-Domain Provider]
    외부 도메인(Policy 등)에서 하드웨어 설계도 정보에 접근하는 엄밀한 통로입니다.
    모든 반환값은 DB 모델이 아닌 Pydantic 스키마 형태입니다.
    """
    def get_blueprint_by_id(self, db: Session, *, id: int) -> Optional[HardwareBlueprintRead]:
        """ID로 하드웨어 블루프린트를 조회합니다."""
        return hardware_blueprint_query_service.get_blueprint_by_id(db, id=id)
    
    def get_blueprint_recipe(self, db: Session, *, blueprint_id: int) -> List[BlueprintPinMappingRead]:
        """특정 설계도에 정의된 물리적 핀 배선 정보 리스트를 조회합니다."""
        return hardware_blueprint_query_service.get_blueprint_recipe(db, blueprint_id=blueprint_id)
    
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
        """특정 블루프린트에 대해 유효한 부품(supported_component) ID 목록을 조회합니다."""
        return hardware_blueprint_query_service.get_valid_component_ids_for_blueprint(db, blueprint_id=blueprint_id)

    def is_component_valid_for_blueprint(self, db: Session, *, blueprint_id: int, supported_component_id: int) -> bool:
        """특정 블루프린트에 대해 특정 부품이 유효한지 확인합니다."""
        return hardware_blueprint_query_service.is_component_valid_for_blueprint(db, blueprint_id=blueprint_id, supported_component_id=supported_component_id)
    
    def get_valid_pin_pool(self, db: Session, *, blueprint_id: int, pin_type: str = 'GPIO') -> List[int]:
        """[Inter-Domain] 설계도의 가용 핀 풀 정보를 정책 계층에 재수출합니다."""
        return hardware_blueprint_query_service.get_valid_pin_pool(
            db, blueprint_id=blueprint_id, pin_type=pin_type
        )
hardware_blueprint_query_provider = HardwareBlueprintQueryProvider()
