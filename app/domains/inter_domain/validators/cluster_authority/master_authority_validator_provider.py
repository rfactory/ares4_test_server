from typing import Tuple, Optional
from app.models.objects.device import Device
from app.models.objects.system_unit import SystemUnit
from app.domains.action_authorization.validators.cluster_authority.master_authority_validator import MasterAuthorityValidator

class MasterAuthorityValidatorProvider:
    """[Inter-Domain] 시스템 유닛 마스터 권한 검증 공급자"""
    def __init__(self):
        self._validator = MasterAuthorityValidator()

    def validate(self, device: Device, unit: SystemUnit) -> Tuple[bool, Optional[str]]:
        return self._validator.validate(device, unit)

master_authority_validator_provider = MasterAuthorityValidatorProvider()