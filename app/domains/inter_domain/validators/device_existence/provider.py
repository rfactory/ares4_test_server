# inter_domain/validators/device_existence/provider.py

from sqlalchemy.orm import Session
from typing import Tuple, Optional

# Validator 임포트
from app.domains.action_authorization.validators.device_existence.validator import device_existence_validator

class DeviceExistenceValidatorProvider:
    """
    DeviceExistenceValidator의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def validate(
        self,
        db: Session,
        *,
        device_uuid_str: str
    ) -> Tuple[bool, Optional[str]]:
        """
        주어진 UUID로 장치가 DB에 실제로 존재하는지 확인하는 '판단'을 위임합니다.
        """
        return device_existence_validator.validate(
            db=db,
            device_uuid_str=device_uuid_str
        )

device_existence_validator_provider = DeviceExistenceValidatorProvider()
