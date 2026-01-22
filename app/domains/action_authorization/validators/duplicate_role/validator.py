from app.models.objects.role import Role
from app.core.exceptions import AppLogicError

class DuplicateRoleValidator:
    """
    [Validator]
    두 역할이 동일한지 판단하는 순수 Validator입니다.
    """
    def validate(self, *, old_role: Role, new_role: Role):
        """두 역할의 ID가 동일하면 에러를 발생시킵니다."""
        if old_role.id == new_role.id:
            raise AppLogicError("User already has this role.")

duplicate_role_validator = DuplicateRoleValidator()