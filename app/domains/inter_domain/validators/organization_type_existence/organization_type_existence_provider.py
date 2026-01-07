from sqlalchemy.orm import Session

from app.domains.action_authorization.validators.organization_type_existence.validator import validate_organization_type_exists

class OrganizationTypeExistenceValidatorProvider:
    """
    `validate_organization_type_exists` validator의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def validate(self, db: Session, *, organization_type_id: int) -> bool:
        """
        주어진 조직 유형 ID가 유효한지 검증합니다.
        """
        return validate_organization_type_exists.validate(
            db, organization_type_id=organization_type_id
        )

organization_type_existence_provider = OrganizationTypeExistenceValidatorProvider()
