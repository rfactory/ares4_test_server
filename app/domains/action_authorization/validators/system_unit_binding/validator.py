from typing import Optional
from app.models.objects.device import Device
from app.models.objects.system_unit import SystemUnit
from app.core.exceptions import ValidationError, PermissionDeniedError, NotFoundError, AppLogicError

class SystemUnitBindingValidator:
    """[The Judge] 오직 Policy가 제공한 정보를 기반으로 '적합성'만 판정합니다."""

    def validate_binding_eligibility(
        self, *, 
        actor_user_id: int, 
        device_obj: Device,
        unit_obj: SystemUnit,
        is_unit_owner: bool,
        current_device_count: int,
        requested_role: str,
        has_existing_master: bool
    ) -> bool:
        if not device_obj: raise NotFoundError("Device", "기기를 찾을 수 없습니다.")
        if not unit_obj: raise NotFoundError("SystemUnit", "유닛을 찾을 수 없습니다.")

        if device_obj.owner_user_id != actor_user_id:
            raise PermissionDeniedError("기기 소유권이 없습니다.")
        if not is_unit_owner:
            raise PermissionDeniedError("유닛 관리 권한이 없습니다.")

        if device_obj.system_unit_id is not None:
            raise ValidationError(f"기기 {device_obj.id}는 이미 유닛 {device_obj.system_unit_id}에 귀속되어 있습니다.")

        required_limit = unit_obj.product_line.required_block_count if unit_obj.product_line else 0
        if current_device_count >= required_limit:
            raise ValidationError(f"유닛 {unit_obj.id}의 정원({required_limit}대)이 이미 충족되었습니다.")

        if requested_role == "MASTER" and has_existing_master:
            raise ValidationError("유닛에 이미 마스터(반장)가 존재합니다.")
        return True

    def validate_promotion_eligibility(
        self, *, unit_id: int, target_device: Optional[Device], device_id: int
    ) -> bool:
        """[The Judge] 마스터 승격 권한 및 논리적 타당성을 판정합니다."""
        if not target_device:
            raise NotFoundError("Device", f"ID {device_id}")
        
        if target_device.system_unit_id != unit_id:
            raise AppLogicError(f"기기 {device_id}가 유닛 {unit_id}에 속해있지 않아 반장이 될 수 없습니다.")
        return True
    
    def validate_unbinding_eligibility(
        self, *, 
        actor_user_id: int, 
        device_obj: Device, 
        is_unit_owner: bool
    ) -> bool:
        """[The Judge] 기기 결합 해제 권한 및 상태를 판정합니다."""
        # 1. 존재 여부 확인
        if not device_obj: 
            raise NotFoundError("Device", "기기를 찾을 수 없습니다.")

        # 2. 소유권/권한 검증
        if device_obj.owner_user_id != actor_user_id:
            raise PermissionDeniedError("기기 소유권이 없습니다.")
        if not is_unit_owner:
            raise PermissionDeniedError("유닛 관리 권한이 없습니다.")

        # 3. 상태 검증 (이미 해제된 상태인지 판단)
        if device_obj.system_unit_id is None:
            raise ValidationError(f"기기 {device_obj.id}는 이미 어느 유닛에도 속해있지 않습니다.")

        return True

system_unit_binding_validator = SystemUnitBindingValidator()