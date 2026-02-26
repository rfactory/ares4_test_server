from typing import Optional
from app.models.objects.device import Device
from app.models.objects.system_unit import SystemUnit
from app.domains.action_authorization.validators.system_unit_binding.validator import system_unit_binding_validator

class SystemUnitBindingValidatorProvider:
    """[Inter-Domain Judge] Policy 계층에 판단 서비스 제공 (IDE 자동 완성 지원 버전)"""
    
    def validate_binding_eligibility(self, **kwargs) -> bool:
        # [기존 유지] 가변 인자를 유지하되 내부에서 호출
        return system_unit_binding_validator.validate_binding_eligibility(**kwargs)

    def validate_promotion_eligibility(self, *, unit_id: int, target_device: Optional[Device], device_id: int) -> bool:
        """이름이 명시되어야 Policy에서 '흰색'으로 나오지 않습니다."""
        return system_unit_binding_validator.validate_promotion_eligibility(
            unit_id=unit_id, target_device=target_device, device_id=device_id
        )
    
    def validate_unbinding_eligibility(
        self, *, 
        actor_user_id: int, 
        device_obj: Device, 
        is_unit_owner: bool
    ) -> bool:
        """해제 판단은 새로 추가하는 것이니 인자를 명시해서 Policy의 '흰색 에러'를 방지합니다."""
        return system_unit_binding_validator.validate_unbinding_eligibility(
            actor_user_id=actor_user_id,
            device_obj=device_obj,
            is_unit_owner=is_unit_owner
        )

system_unit_binding_validator_provider = SystemUnitBindingValidatorProvider()