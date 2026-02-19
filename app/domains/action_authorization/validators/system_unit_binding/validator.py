from typing import Optional
from app.models.objects.device import Device
from app.models.objects.system_unit import SystemUnit
from app.core.exceptions import ValidationError, PermissionDeniedError, NotFoundError

class SystemUnitBindingValidator:
    """
    [The Judge]
    정확한 타입을 명시하여 IDE의 흰색 표시를 해결하고 자동 완성을 활성화합니다.
    """

    def validate_binding_eligibility(
    self, 
    *, 
    actor_user_id: int, 
    device_obj: Device,
    unit_obj: SystemUnit,
    is_unit_owner: bool,
    current_device_count: int,
    max_capacity: int,
    requested_role: str,
    has_existing_master: bool
) -> bool:
        
        # 1. 존재 여부 확인
        if not device_obj:
            raise NotFoundError("Device", "기기를 찾을 수 없습니다.")
        if not unit_obj:
            raise NotFoundError("SystemUnit", "유닛을 찾을 수 없습니다.")

        # 2. 소유권 검증 (이제 .owner_user_id에 색상이 들어오고 자동 완성이 됩니다)
        if device_obj.owner_user_id != actor_user_id:
            raise PermissionDeniedError("해당 기기에 대한 소유권이 없습니다.")
        
        # 유닛 소유권 확인
        if not is_unit_owner:
            raise PermissionDeniedError("이 시스템 유닛을 관리할 권한이 없습니다.")

        # 3. 기기 가용성 확인 (이미 다른 유닛에 박혀있는지)
        if device_obj.system_unit_id is not None:
            raise ValidationError(f"이 기기는 이미 유닛(ID: {device_obj.system_unit_id})에 할당되어 있습니다.")

        # 4. 유닛 수용량 검증
        if current_device_count >= max_capacity:
            raise ValidationError(f"유닛 수용량({max_capacity}개)이 초과되었습니다.")

        # 5. 마스터 역할 중복 검증
        if requested_role == "MASTER" and has_existing_master:
            raise ValidationError("이 유닛에는 이미 마스터 기기가 존재합니다.")

        return True

system_unit_binding_validator = SystemUnitBindingValidator()