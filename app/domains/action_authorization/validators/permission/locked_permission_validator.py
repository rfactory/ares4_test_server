from typing import List

from app.core.exceptions import PermissionDeniedError
from app.models.objects.permission import Permission

class LockedPermissionValidator:
    def validate(self, *, changed_permissions: List[Permission]) -> None:
        """변경될 권한 목록에 시스템 잠금 권한이 포함되어 있는지 확인합니다."""
        for perm in changed_permissions:
            if perm.is_system_locked:
                raise PermissionDeniedError(f"Cannot modify system-locked permission: '{perm.name}'.")

locked_permission_validator = LockedPermissionValidator()