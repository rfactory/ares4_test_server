import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.objects.user import User # For actor_user to audit logs
from app.domains.inter_domain.certificate_management.certificate_command_provider import certificate_command_provider
from app.domains.inter_domain.validators.existing_certificate_validity_provider import existing_certificate_validity_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider # Import audit provider

logger = logging.getLogger(__name__)

class ServerCertificateAcquisitionPolicy:
    """
    서버가 MQTT 브로커와 통신하기 위한 유효한 클라이언트 인증서를 획득하는 정책입니다.
    - 기존 인증서의 유효성을 검증하고,
    - 유효하지 않거나 만료가 임박하면 새로운 인증서를 발급받습니다.
    - 시스템 사용자(ID 1)를 사용하여 감사 로그를 기록합니다.
    """
    SYSTEM_USER_ID = 1 # ID 1은 시스템 사용자에게 할당되어야 합니다.

    def acquire_valid_server_certificate(self, db: Session, current_cert_data: Optional[Dict]) -> Dict:
        """
        서버가 사용할 유효한 클라이언트 인증서를 획득하고, 이 과정을 감사 로그로 기록합니다.
        
        Args:
            db: 데이터베이스 세션. 시스템 사용자 조회 및 감사 로그 기록에 사용됩니다.
            current_cert_data: 현재 서버가 가지고 있는 인증서 데이터 (Vault 응답 형식).
                               없거나 유효하지 않으면 새로운 인증서가 발급됩니다.

        Returns:
            유효한 클라이언트 인증서 데이터 (Dict).
        """
        system_user = db.query(User).filter(User.id == self.SYSTEM_USER_ID).first()
        if not system_user:
            logger.error(f"System user with ID {self.SYSTEM_USER_ID} not found. Proceeding with None actor_user for audit logs.")
            system_user = None # Fallback to None if system user is not found

        final_cert_data = None
        event_type = ""
        description = ""
        details = {}

        # 1. 기존 인증서 유효성 검증
        is_valid, validation_message = False, "No current certificate data."
        if current_cert_data:
            is_valid, validation_message = existing_certificate_validity_provider.validate(current_cert_data)

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
            # 2. 유효하지 않으면 새로운 인증서 발급
            # issue_server_mqtt_cert는 이미 감사 로그를 포함합니다.
            final_cert_data = certificate_command_provider.issue_server_mqtt_cert(db=db, actor_user=system_user)
            logger.info("New server MQTT client certificate issued successfully.")
            event_type = "SERVER_CERTIFICATE_ACQUIRED_NEW"
            description = "Server acquired a new MQTT client certificate due to invalidity or expiry."
            details = {
                "serial_number": final_cert_data.get("serial_number"),
                "common_name": final_cert_data.get("common_name"),
                "reason": validation_message,
                "status": "newly_acquired"
            }
        
        # Policy 레벨 감사 로그 기록: 서버가 유효한 인증서를 획득한 비즈니스 이벤트 기록
        audit_command_provider.log(
            db=db,
            actor_user=system_user,
            event_type=event_type,
            description=description,
            details=details
        )
        
        return final_cert_data

server_certificate_acquisition_policy = ServerCertificateAcquisitionPolicy()
