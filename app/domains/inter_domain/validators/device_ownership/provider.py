from sqlalchemy.orm import Session
from typing import Tuple, Optional

from app.domains.inter_domain.device_management.schemas.device_query import DeviceRead
from app.domains.action_authorization.validators.device_ownership.validator import device_ownership_validator
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider

class DeviceOwnershipValidatorProvider:
    def validate_access(self, db: Session, *, user_email: str, device: DeviceRead, access: str):
        # 1. 유저 정보 조회
        user = user_identity_query_provider.get_user_by_email(db, email=user_email)
        if not user: return False, "User not found"

        # 2. 유저가 속한 모든 조직 ID 리스트 조회 (판단을 위한 재료 준비)
        # 예시: user_identity_query_provider에 관련 메서드가 있다고 가정
        user_orgs = user_identity_query_provider.get_user_organizations(db, user_id=user.id)
        org_ids = [org.id for org in user_orgs]

        # 3. 순수 발리데이터 호출 (판단만 부탁함)
        return device_ownership_validator.validate(
            user_id=user.id,
            user_org_ids=org_ids,
            device=device,
            access=access
        )

device_ownership_validator_provider = DeviceOwnershipValidatorProvider()