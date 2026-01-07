from sqlalchemy.orm import Session
from typing import List

from app.models.objects.user import User
from app.models.objects.role import Role
from app.domains.action_authorization.validators.last_org_admin.last_org_admin_validator import last_org_admin_validator

class LastOrgAdminValidatorProvider:
    def validate(self, db: Session, *, target_user: User, roles_to_revoke: List[Role]):
        """
        조직의 마지막 관리자 이탈 방지 규칙을 검증합니다.
        """
        return last_org_admin_validator.validate(
            db=db, 
            target_user=target_user, 
            roles_to_revoke=roles_to_revoke
        )

last_org_admin_validator_provider = LastOrgAdminValidatorProvider()
