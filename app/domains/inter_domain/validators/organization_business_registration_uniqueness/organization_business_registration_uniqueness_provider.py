from sqlalchemy.orm import Session

from app.domains.action_authorization.validators.organization_business_registration_uniqueness.validator import validate_unique_business_registration

class OrganizationBusinessRegistrationUniquenessValidatorProvider:
    """
    `validate_unique_business_registration` validator의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def validate(self, db: Session, *, business_registration_number: str) -> bool:
        """
        주어진 사업자 등록 번호가 유일한지 검증합니다.
        """
        return validate_unique_business_registration.validate(
            db, business_registration_number=business_registration_number
        )

organization_business_registration_uniqueness_provider = OrganizationBusinessRegistrationUniquenessValidatorProvider()
