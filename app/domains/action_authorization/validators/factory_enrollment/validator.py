import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from app.core.exceptions import AuthenticationError, ValidationError

if TYPE_CHECKING:
    from app.models.objects.provisioning_token import ProvisioningToken

logger = logging.getLogger(__name__)

class FactoryEnrollmentValidator:
    """
    [판단 계층] 공장 기기 등록 및 QR 점유에 필요한 모든 논리적 검증을 수행합니다.
    I/O 없이 전달받은 데이터만으로 True/False 혹은 에러 발생 여부를 판단합니다.
    """

    # --- 1. [Existing] 공장 네트워크 신뢰성 검증 ---

    def validate_network_trust(self, client_ip: str, trusted_ips: List[str]) -> bool:
        """요청 IP가 화이트리스트에 포함된 신뢰할 수 있는 공장 내부 IP인지 확인합니다."""
        return client_ip in trusted_ips
    
    def validate_network_trust_or_raise(self, client_ip: str, trusted_ips: List[str]):
        """신뢰할 수 없는 IP일 경우 즉시 AuthenticationError를 발생시킵니다."""
        if not self.validate_network_trust(client_ip, trusted_ips):
            raise AuthenticationError(f"Untrusted network access from {client_ip}")

    # --- 2. [Existing] 기기 및 패키지 검증 ---

    def validate_device_availability(self, device_exists: bool) -> bool:
        """기기가 이미 시스템에 등록되어 있는지 여부를 판단합니다."""
        # 이미 존재하면 새 기기로 등록할 수 없으므로 False 반환
        return not device_exists

    def validate_identity_package(self, package: dict) -> bool:
        """발급된 신분증 패키지에 UUID, 인증서, 개인키, CA 체인이 모두 포함되었는지 검증합니다."""
        required_fields = ["uuid", "cert", "key", "ca"]
        return all(field in package for field in required_fields)

    # --- 3. [New] QR 토큰(Provisioning Token) 검증 ---

    def validate_token_for_claim(self, token: "ProvisioningToken"):
        """
        사용자가 제출한 QR 토큰이 사용 가능한지 Policy로부터 넘겨받아 검사합니다.
        
        검증 항목:
        1. 이미 사용된 토큰인가? (중복 점유 차단)
        2. 유효 기간이 만료되었는가? (만료된 티켓 거부)
        """
        # 1. 상태 체크
        if token.is_used:
            raise ValidationError(
                detail="This provisioning token has already been used.",
                code="TOKEN_ALREADY_USED"
            )

        # 2. 유효 기간 체크
        # DB의 expires_at과 현재 UTC 시간을 비교합니다.
        now = datetime.now(timezone.utc)
        if token.expires_at < now:
            raise ValidationError(
                detail="This provisioning token has expired.",
                code="TOKEN_EXPIRED"
            )
        
        return True

# 싱글톤 인스턴스
factory_enrollment_validator = FactoryEnrollmentValidator()