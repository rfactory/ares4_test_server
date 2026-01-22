from app.models.objects.role import Role
from app.domains.action_authorization.validators.duplicate_role.validator import duplicate_role_validator

class DuplicateRoleValidatorProvider:
    def validate(self, *, old_role: Role, new_role: Role):
        return duplicate_role_validator.validate(old_role=old_role, new_role=new_role)

duplicate_role_validator_provider = DuplicateRoleValidatorProvider()
