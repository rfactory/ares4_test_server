from sqlalchemy.orm import Session

class FactoryIdentityService:
    """
    [수행 계층] 공장 등록 도메인만의 특화된 물리적 작업을 수행합니다.
    다른 도메인(Device, Cert)의 일반적인 작업은 Policy가 해당 도메인을 직접 호출하므로,
    이 서비스는 공장 등록 특유의 보조 로직만 담습니다.
    """

    def prepare_factory_metadata(self, cpu_serial: str):
        """공장 등록 시 필요한 메타데이터를 준비합니다."""
        # 공장 등록 시에만 필요한 특수 메타데이터 구성 로직 (예시)
        return {"provisioned_at_factory": True, "initial_serial": cpu_serial}