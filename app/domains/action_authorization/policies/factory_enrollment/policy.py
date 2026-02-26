import logging
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.core.exceptions import NotFoundError, PermissionDeniedError

# 도메인 서비스 및 검증기 프로바이더
# 1. 검증기
from app.domains.inter_domain.validators.factory_enrollment.provider import factory_enrollment_validator_provider

# 2. 기기 관리 (기존 Auto-Enroll용)
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider
from app.domains.inter_domain.device_management.device_command_provider import device_management_command_provider
from app.domains.inter_domain.hardware_blueprint.hardware_blueprint_command_provider import hardware_blueprint_command_provider

# 3. 토큰 & 할당 (신규 Claim용)
from app.domains.inter_domain.provisioning_token.provisioning_token_query_provider import provisioning_token_query_provider
from app.domains.inter_domain.provisioning_token.provisioning_token_command_provider import provisioning_token_command_provider
from app.domains.inter_domain.system_unit_assignment.system_unit_assignment_command_provider import system_unit_assignment_command_provider
from app.domains.inter_domain.system_unit_assignment.system_unit_assignment_query_provider import system_unit_assignment_query_provider

# 4. 감사 로그
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

# 5. 인증서 관리 (Vault PKI 연동)
from app.domains.inter_domain.certificate_management.certificate_command_provider import certificate_command_provider

# 6. 모델
from app.models.objects.device import Device as DBDevice

logger = logging.getLogger(__name__)

class FactoryEnrollmentPolicy:
    """
    [지휘 계층] 공장 등록 및 사용자 기기 점유 프로세스를 조율하는 오케스트레이터입니다.
    """

    async def execute_factory_enrollment(self, db: Session, client_ip: str, cpu_serial: str, trusted_ips: list[str], **kwargs):
        """[Existing] 기기 자동 등록 (Device -> Server)"""
        try:
            validator = factory_enrollment_validator_provider.get_validator()
            validator.validate_network_trust_or_raise(client_ip, trusted_ips)
            
            query_svc = device_management_query_provider.get_service()
            query_svc.ensure_device_is_enrollee(db, serial=cpu_serial)

            cmd_svc = device_management_command_provider.get_service()
            # [Step 4] 기기 정체성 생성 (UUID, HMAC 등)
            identity_package = await cmd_svc.execute_factory_enrollment_transaction(
                db=db, cpu_serial=cpu_serial, client_ip=client_ip, **kwargs
            )

            # [보완] Policy 수준에서 감사 로그의 상세도 강화
            audit_command_provider.log_event(
                db=db,
                event_type="FACTORY_ENROLLMENT_SUCCESS",
                description=f"Identity and mTLS Credentials granted: {cpu_serial}",
                details={
                    "device_id": identity_package["device_id"],
                    "certificate_issued": True # Service에서 이미 발급됨
                }
            )

            db.commit() 
            logger.info(f"✅ [Policy] Database COMMIT successful for {cpu_serial}")
            return identity_package

        except Exception as e:
            db.rollback()
            self._audit_failure(db, cpu_serial, client_ip, e)
            raise e
    
    def claim_unit(self, db: Session, token_value: str, claimer_user_id: int) -> Dict[str, Any]:
        """
        [User Scenario] QR 토큰을 사용하여 시스템 유닛의 소유권을 사용자에게 할당합니다.
        실제 기기(Device)와의 물리적 연결 및 핀맵 복제는 별도의 연결 로직에서 처리합니다.
        """
        try:
            # 1. 토큰 데이터 조회
            token = provisioning_token_query_provider.get_by_value(db, token_value)
            if not token:
                raise NotFoundError(resource_name="ProvisioningToken", resource_id=token_value)

            # 2. 순수 로직 검증 (Validator)
            validator = factory_enrollment_validator_provider.get_validator()
            validator.validate_token_for_claim(token)
            
            # 3. 소유권 할당 (OWNER 권한 부여)
            assignment = system_unit_assignment_command_provider.assign_owner(
                db=db, 
                unit_id=token.system_unit_id, 
                user_id=claimer_user_id
            )

            # 4. 토큰 상태 업데이트 (상태만 '사용됨'으로 변경)
            provisioning_token_command_provider.mark_as_used(
                db=db, 
                token_id=token.id
            )

            # 5. 감사 로그 기록
            audit_command_provider.log_event(
                db=db,
                event_type="UNIT_CLAIM_SUCCESS",
                description=f"User {claimer_user_id} claimed unit {token.system_unit_id}",
                details={"unit_id": token.system_unit_id, "claimer_id": claimer_user_id}
            )

            # 6. [최종 확정]
            db.commit()
            logger.info(f"✅ [Policy] Unit {token.system_unit_id} successfully claimed by User {claimer_user_id}")

            return {
                "status": "success",
                "message": "System Unit claimed successfully.",
                "unit_id": assignment.system_unit_id,
                "role": assignment.role
            }

        except Exception as e:
            db.rollback()
            # 실패 기록 감사 로그 (선택 사항)
            logger.error(f"❌ [Policy] Unit claim failed: {str(e)}")
            raise e
    
    def verify_device_identity_or_raise(self, db: Session, *, cpu_serial: str, device_uuid: str) -> DBDevice:
        """
        [Handshake Judge] 반환 타입을 DBDevice로 명시하여 IDE의 '흰색 에러'를 해결합니다.
        """
        device = device_management_query_provider.get_service().device_query_crud.get_by_serial(db, serial=cpu_serial)
        if not device or device.current_uuid != device_uuid:
            raise PermissionDeniedError("인증되지 않은 하드웨어 정보입니다.")
        return device
        
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