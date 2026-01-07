from sqlalchemy.orm import Session
from typing import Optional

from app.models.objects.user import User
from app.domains.action_authorization.validators.permission.validator import permission_validator

class PermissionValidatorProvider:
    def validate(self, db: Session, *, user: User, permission_name: str, organization_id: Optional[int] = None) -> None:
        """Validator의 validate 메소드를 호출합니다."""
        permission_validator.validate(
            db=db, user=user, permission_name=permission_name, organization_id=organization_id
        )

permission_validator_provider = PermissionValidatorProvider()