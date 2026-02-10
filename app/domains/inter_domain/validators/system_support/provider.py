from typing import Tuple, Optional
from app.domains.action_authorization.validators.system_support.validator import system_support_validator
from app.domains.inter_domain.supported_component_management.schemas.models import SupportedComponentRead

class SystemSupportValidatorProvider:
    def validate(self, *, supported_component: Optional[SupportedComponentRead]) -> Tuple[bool, Optional[str]]:
        """판단 전문가에게 데이터를 전달합니다."""
        return system_support_validator.validate_support(supported_component=supported_component)

system_support_validator_provider = SystemSupportValidatorProvider()