import logging
from typing import Tuple, Optional, Any

# 실제 로직을 담고 있는 Validator 임포트
from app.domains.action_authorization.validators.image_ingestion.image_ingestion_validator import image_ingestion_validator

logger = logging.getLogger(__name__)

class ImageIngestionValidatorProvider:
    def validate_all(
        self, 
        *, 
        device: Optional[Any], 
        image_bytes: bytes, 
        payload: dict
    ) -> Tuple[bool, Optional[str]]:
        """
        [Ares Aegis] 인터도메인 이미지 검증 인터페이스
        - Policy가 징집한 데이터를 바탕으로 유효성 여부(Yes/No)만 판단합니다.
        - 실제 판단 로직은 Action Authorization 도메인의 Validator에 위임합니다.
        """
        return image_ingestion_validator.validate_all(
            device=device,
            image_bytes=image_bytes,
            payload=payload
        )

# 싱글톤 인스턴스 노출
image_ingestion_validator_provider = ImageIngestionValidatorProvider()