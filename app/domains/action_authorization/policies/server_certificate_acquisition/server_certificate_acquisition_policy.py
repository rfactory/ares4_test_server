import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.domains.inter_domain.certificate_management.certificate_command_provider import certificate_command_provider
from app.domains.inter_domain.validators.existing_certificate_validity_provider import existing_certificate_validity_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class ServerCertificateAcquisitionPolicy:
    """
    서버가 MQTT 브로커와 통신하기 위한 유효한 클라이언트 인증서를 획득하는 정책입니다.
    - 기존 인증서의 유효성을 검증하고, 만료 임박 시 새 인증서를 발급합니다.
    - AuditCommandService의 로직에 따라 actor_user=None 전달 시 자동으로 System(ID 1)으로 기록됩니다.
    """

    def acquire_valid_server_certificate(self, db: Session, current_cert_data: Optional[Dict]) -> Dict:
        """
        서버가 사용할 유효한 클라이언트 인증서를 획득하고 감사 로그를 기록합니다.
        """
        final_cert_data = None
        event_type = ""
        description = ""
        details = {}

        try:
            # 1. 기존 인증서 유효성 검증
            is_valid, validation_message = False, "No current certificate data."
            if current_cert_data:
                is_valid, validation_message = existing_certificate_validity_provider.validate(current_cert_data)

            # 2. 비즈니스 로직 분기
            if is_valid:
                logger.info("Current server MQTT client certificate is still valid. Reusing existing certificate.")
                final_cert_data = current_cert_data
                event_type = "SERVER_CERTIFICATE_REUSED"
                description = "Server reused existing valid MQTT client certificate."
                details = {
                    "serial_number": final_cert_data.get("serial_number"),
                    "common_name": final_cert_data.get("common_name"),
                    "status": "reused"
                }
            else:
                logger.warning(f"Server MQTT client certificate invalid or expiring: {validation_message}. Issuing new certificate.")
                
                # 새 인증서 발급 (Provider 호출)
                # actor_user=None을 넘겨도 Audit 서비스에서 시스템 유저로 처리함
                final_cert_data = certificate_command_provider.issue_server_mqtt_cert(db=db, actor_user=None)
                
                logger.info("New server MQTT client certificate issued successfully.")
                event_type = "SERVER_CERTIFICATE_ACQUIRED_NEW"
                description = "Server acquired a new MQTT client certificate due to invalidity or expiry."
                details = {
                    "serial_number": final_cert_data.get("serial_number"),
                    "common_name": final_cert_data.get("common_name"),
                    "reason": validation_message,
                    "status": "newly_acquired"
                }
            
            # 3. 정책 레벨 최종 감사 로그 기록
            audit_command_provider.log(
                db=db,
                actor_user=None, # System 자동 할당
                event_type=event_type,
                description=description,
                details=details
            )

            # [Ares Aegis] 4. 트랜잭션 확정
            db.commit()
            
            return final_cert_data

        except Exception as e:
            logger.error(f"Failed to acquire server certificate: {e}", exc_info=True)
            db.rollback()
            raise e

# 싱글톤 인스턴스 생성
server_certificate_acquisition_policy = ServerCertificateAcquisitionPolicy()