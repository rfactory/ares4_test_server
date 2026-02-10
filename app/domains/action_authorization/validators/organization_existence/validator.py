import logging
from sqlalchemy.orm import Session
from typing import Tuple, Optional

from app.models.objects.organization import Organization
from app.domains.inter_domain.organizations.organization_query_provider import organization_query_provider

logger = logging.getLogger(__name__)

class OrganizationExistenceValidator:
    def validate(self, db: Session, *, registration_number: str) -> Tuple[bool, Optional[Organization]]:
        """
        주어진 사업자 등록 번호로 조직이 존재하는지 확인합니다.
        조직이 존재하면 (True, organization_object)를, 존재하지 않으면 (False, None)을 반환합니다.
        """
        organization = organization_query_provider.get_organization_entry_by_registration_number(
            db, 
            registration_number=registration_number
        )
        
        if organization:
            logger.info(f"Validation check: Organization with registration number '{registration_number}' already exists.")
            return True, organization
        else:
            logger.warning(f"Validation check: Organization with registration number '{registration_number}' does not exist.")
            return False, None

organization_existence_validator = OrganizationExistenceValidator()
