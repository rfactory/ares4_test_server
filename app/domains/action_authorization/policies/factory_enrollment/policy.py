import logging
from sqlalchemy.orm import Session

# 도메인 서비스 및 검증기 프로바이더
from app.domains.inter_domain.validators.factory_enrollment.provider import factory_enrollment_validator_provider
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider
from app.domains.inter_domain.device_management.device_command_provider import device_management_command_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class FactoryEnrollmentPolicy:
    """
    [지휘 계층] 공장 등록 프로세스를 조율하는 오케스트레이터입니다.
    직접 값을 생성하거나 기술적인 상세 구현을 하지 않으며, 서비스 계층에 '판단'과 '수행'을 요청합니다.
    """

    async def execute_factory_enrollment(
        self, 
        db: Session, 
        client_ip: str, 
        cpu_serial: str, 
        trusted_ips: list[str],
        target_unit_name: str = None,   # 추가됨: 유닛 이름
        components: list[str] = None,   # 추가됨: 부품 리스트
        auto_activate: bool = False     # 추가됨: 자동 활성화 여부
    ):
        try:
            # 1. [검증기 위임] 네트워크 신뢰성 판단
            # "이 IP가 믿을만한지 니가 판단해줘"
            validator = factory_enrollment_validator_provider.get_validator()
            validator.validate_network_trust_or_raise(client_ip, trusted_ips)

            # 2. [쿼리 서비스 위임] 기기 중복 여부 확인
            # "이 시리얼 번호가 이미 등록되어 있는지 확인해줘"
            query_svc = device_management_query_provider.get_service()
            query_svc.ensure_device_is_enrollee(db, serial=cpu_serial)

            # 3. [커맨드 서비스 위임] 정체성 생성 및 등록 프로세스 일괄 수행
            # "공장 전용 등록 절차(UUID/HMAC/DB/Cert/Vault)를 트랜잭션으로 처리해줘"
            cmd_svc = device_management_command_provider.get_service()
            identity_package = await cmd_svc.execute_factory_enrollment_transaction(
                db=db, 
                cpu_serial=cpu_serial,
                client_ip=client_ip,
                target_unit_name=target_unit_name, # 전달!
                components=components,             # 전달!
                auto_activate=auto_activate        # 전달!
            )

            # 4. [감사 로그 위임] 최종 성공 기록
            # "감사 시스템에 이 성공 사실을 남겨줘"
            audit_command_provider.log_event(
                db=db,
                event_type="FACTORY_ENROLLMENT_SUCCESS",
                description=f"Initial identity granted to serial: {cpu_serial}",
                details={"client_ip": client_ip, "device_id": identity_package["device_id"]}
            )

            db.commit()
            return identity_package

        except Exception as e:
            db.rollback()
            # 실패 시 로그 기록도 감사 서비스에 위임할 수 있습니다.
            self._audit_failure(db, cpu_serial, client_ip, e)
            raise e

    def _audit_failure(self, db: Session, serial: str, ip: str, error: Exception):
        """실패 기록을 별도 트랜잭션으로 처리하는 감사 로직"""
        try:
            audit_command_provider.log_event(
                db=db,
                event_type="FACTORY_ENROLLMENT_FAILED",
                description=str(error),
                details={"cpu_serial": serial, "client_ip": ip},
                log_level="WARNING"
            )
            db.commit()
        except Exception as log_e:
            logger.error(f"Audit failed: {log_e}")

factory_enrollment_policy = FactoryEnrollmentPolicy()