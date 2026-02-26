from typing import Optional, Any
from app.domains.action_authorization.validators.system_unit_unbinding.validator import system_unit_unbinding_validator

class SystemUnitUnbindingValidatorProvider:
    """[Inter-Domain Bridge] 해지 판단 로직을 Policy 계층에 중계합니다."""

    def validate_unbinding_ownership(self, *, assignment: Optional[Any]) -> bool:
        """소유권 해지 자격 판정 중계"""
        return system_unit_unbinding_validator.validate_unbinding_ownership(
            assignment=assignment
        )

system_unit_unbinding_validator_provider = SystemUnitUnbindingValidatorProvider()