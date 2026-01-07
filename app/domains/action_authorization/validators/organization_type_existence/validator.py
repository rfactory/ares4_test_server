from sqlalchemy.orm import Session

from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider

class ValidateOrganizationTypeExists:
    def validate(self, db: Session, *, organization_type_id: int) -> bool:
        """
        주어진 조직 유형 ID가 유효한지 확인합니다.

        - 유효한 경우 (조직 유형이 존재함): True
        - 유효하지 않은 경우 (조직 유형이 없음): False
        """
        org_type = organization_query_provider.get_organization_type_by_id(
            db, id=organization_type_id
        )
        return org_type is not None

validate_organization_type_exists = ValidateOrganizationTypeExists()
