# inter_domain/validators/device_attachment/provider.py

from sqlalchemy.orm import Session
from typing import Tuple, Optional

# Validator 임포트
from app.domains.action_authorization.validators.device_attachment.validator import device_attachment_validator

class DeviceAttachmentValidatorProvider:
    """
    DeviceAttachmentValidator의 기능을 외부 도메인에 노출하는 제공자입니다.
    """
    def validate(
        self,
        db: Session,
        *,
        device_id: int,
        supported_component_id: int,
        instance_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        특정 부품 인스턴스가 장치에 연결되도록 사용자가 설정했는지 '판단'을 위임합니다.
        """
        return device_attachment_validator.validate(
            db=db,
            device_id=device_id,
            supported_component_id=supported_component_id,
            instance_name=instance_name
        )

device_attachment_validator_provider = DeviceAttachmentValidatorProvider()
