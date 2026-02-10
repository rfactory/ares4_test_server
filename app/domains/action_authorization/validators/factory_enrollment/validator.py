from app.core.exceptions import AuthenticationError

class FactoryEnrollmentValidator:
    """
    [판단 계층] 공장 기기 등록에 필요한 논리적 검증을 수행합니다.
    이 계층은 외부 상태(DB, API)에 의존하지 않으며, 오직 인자로 받은 데이터만으로 True/False를 판단합니다.
    """

    def validate_network_trust(self, client_ip: str, trusted_ips: list[str]) -> bool:
        """요청 IP가 화이트리스트에 포함된 신뢰할 수 있는 공장 내부 IP인지 확인합니다."""
        return client_ip in trusted_ips
    
    def validate_network_trust_or_raise(self, client_ip: str, trusted_ips: list[str]):
        """
        신뢰할 수 없는 IP일 경우 즉시 AuthenticationError를 발생시킵니다.
        Policy에서 흐름 제어를 단순화하기 위해 사용합니다.
        """
        if not self.validate_network_trust(client_ip, trusted_ips):
            # Policy가 직접 raise 하던 로직을 검증기 안으로 캡슐화합니다.
            raise AuthenticationError(f"Untrusted network access from {client_ip}")

    def validate_device_availability(self, device_exists: bool) -> bool:
        """기기가 이미 시스템에 등록되어 있는지 여부를 판단합니다."""
        # 이미 존재하면 새 기기로 등록할 수 없으므로 False 반환
        return not device_exists

    def validate_identity_package(self, package: dict) -> bool:
        """발급된 신분증 패키지에 UUID, 인증서, 개인키, CA 체인이 모두 포함되었는지 검증합니다."""
        required_fields = ["uuid", "cert", "key", "ca"]
        return all(field in package for field in required_fields)