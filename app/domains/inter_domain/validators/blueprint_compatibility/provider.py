# inter_domain/validators/blueprint_compatibility/provider.py

from sqlalchemy.orm import Session
from typing import Tuple, Optional

# Validator 임포트
from app.domains.action_authorization.validators.blueprint_compatibility.validator import blueprint_compatibility_validator

class BlueprintCompatibilityValidatorProvider:
    """
    BlueprintCompatibilityValidator의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def validate(
        self, db: Session, *, blueprint_id: int, supported_component_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        특정 부품이 하드웨어 청사진과 호환되는지 '판단'을 위임합니다.
        """
        return blueprint_compatibility_validator.validate(
            db=db,
            blueprint_id=blueprint_id,
            supported_component_id=supported_component_id
        )

blueprint_compatibility_validator_provider = BlueprintCompatibilityValidatorProvider()
