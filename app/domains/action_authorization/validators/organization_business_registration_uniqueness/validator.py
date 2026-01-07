from sqlalchemy.orm import Session

from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider

class ValidateUniqueBusinessRegistration:
    def validate(self, db: Session, *, business_registration_number: str) -> bool:
        """
        주어진 사업자 등록 번호가 유일한지 확인합니다.

        - 유니크한 경우 (조직이 없음): True
        - 중복된 경우 (조직이 존재함): False
        """
        existing_org = organization_query_provider.get_organization_by_registration_number(
            db, registration_number=business_registration_number
        )
        return existing_org is None

validate_unique_business_registration = ValidateUniqueBusinessRegistration()
