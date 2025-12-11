import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional

# 필요한 데이터를 조회하기 위해 query_provider를 임포트합니다.
from app.domains.inter_domain.hardware_blueprint.hardware_blueprint_query_provider import hardware_blueprint_query_provider

logger = logging.getLogger(__name__)

class BlueprintCompatibilityValidator:
    def validate(
        self, db: Session, *, blueprint_id: int, supported_component_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        특정 부품이 하드웨어 청사진과 호환되는지 확인하는 단일 책임을 가집니다.
        """
        # 1. query_provider를 통해 부품의 청사진 호환성을 직접 확인합니다.
        is_compatible = hardware_blueprint_query_provider.is_component_valid_for_blueprint(
            db, blueprint_id=blueprint_id, supported_component_id=supported_component_id
        )

        if not is_compatible:
            msg = f"Component ID {supported_component_id} is not compatible with Blueprint ID {blueprint_id}."
            logger.warning(f"VALIDATOR: {msg}")
            return False, msg

        return True, None

blueprint_compatibility_validator = BlueprintCompatibilityValidator()