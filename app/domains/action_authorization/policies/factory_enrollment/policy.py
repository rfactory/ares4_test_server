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

    async def execute_factory_enrollment(self, db: Session, client_ip: str, cpu_serial: str, trusted_ips: list[str], **kwargs):
        try:
            # 1. 검증 및 중복 체크
            validator = factory_enrollment_validator_provider.get_validator()
            validator.validate_network_trust_or_raise(client_ip, trusted_ips)
            
            query_svc = device_management_query_provider.get_service()
            query_svc.ensure_device_is_enrollee(db, serial=cpu_serial)

            # 2. 통합 트랜잭션 수행 (Service의 flush 데이터들이 세션에 대기 중)
            cmd_svc = device_management_command_provider.get_service()
            identity_package = await cmd_svc.execute_factory_enrollment_transaction(
                db=db, cpu_serial=cpu_serial, client_ip=client_ip, **kwargs
            )

            # 3. 감사 로그 기록 (동일 세션 활용)
            audit_command_provider.log_event(
                db=db,
                event_type="FACTORY_ENROLLMENT_SUCCESS",
                description=f"Identity granted: {cpu_serial}",
                details={"device_id": identity_package["device_id"]}
            )

            # 4. [최종 확정] 여기서 딱 한 번!
            db.commit() 
            logger.info(f"✅ [Policy] Database COMMIT successful for {cpu_serial}")
            
            return identity_package

        except Exception as e:
            db.rollback() # 👈 실패 시 모든 흔적 삭제
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