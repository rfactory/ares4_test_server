from typing import List
from app.models.objects.permission import Permission
from app.domains.action_authorization.validators.permission.locked_permission_validator import locked_permission_validator

class LockedPermissionValidatorProvider:
    def validate(self, *, changed_permissions: List[Permission]) -> None:
        return locked_permission_validator.validate(changed_permissions=changed_permissions)

locked_permission_validator_provider = LockedPermissionValidatorProvider()