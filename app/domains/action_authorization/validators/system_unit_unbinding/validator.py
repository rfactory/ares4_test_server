from app.core.exceptions import AccessDeniedError
from typing import Optional, Any

class SystemUnitUnbindingValidator:
    """[The Judge] 유닛 소유권 해지 자격 및 상태를 순수하게 판정합니다."""

    def validate_unbinding_ownership(self, *, assignment: Optional[Any]) -> bool:
        """소유권 할당 정보 존재 여부를 확인하여 해지 가능 여부를 판정합니다."""
        if not assignment:
            raise AccessDeniedError("해당 유닛에 대한 소유권이 없거나 이미 해제되었습니다.")
        
        return True

system_unit_unbinding_validator = SystemUnitUnbindingValidator()