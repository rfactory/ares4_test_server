from typing import Tuple, Optional

# 판단 전문가(Validator) 및 필요한 데이터 규격(Schema) 임포트
from app.domains.action_authorization.validators.device_existence.validator import device_existence_validator
from app.domains.inter_domain.device_management.schemas.device_query import DeviceRead

class DeviceExistenceValidatorProvider:
    """
    내부 도메인의 DeviceExistenceValidator 기능을 외부(Policy 등)에 노출하는 제공자입니다.
    판단에 필요한 데이터는 외부에서 공급받는 것을 원칙으로 합니다.
    """

    def validate_device_existence(
        self,
        *,
        device: Optional[DeviceRead]
    ) -> Tuple[bool, Optional[str]]:
        """
        공급받은 장치 데이터를 바탕으로 존재 및 상태의 적절성을 '판단'하도록 위임합니다.
        
        :param device: Query Provider를 통해 조회된 장치 정보 (없을 경우 None)
        :return: (성공 여부, 에러 메시지)
        """
        # 내부 Validator의 새로운 메서드인 validate_existence를 호출합니다.
        return device_existence_validator.validate_existence(device=device)

# 싱글톤 객체 생성
device_existence_validator_provider = DeviceExistenceValidatorProvider()