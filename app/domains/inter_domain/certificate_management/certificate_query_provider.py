import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session # For audit log if query is audited

from app.models.objects.user import User # For actor_user in audit log
from app.domains.services.certificate_management.repositories.vault_certificate_query_repository import vault_certificate_query_repository
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider # For audit logging sensitive queries

logger = logging.getLogger(__name__)

class CertificateQueryProvider:
    """
    `certificate_management` 도메인의 Query Repository 기능을 외부 도메인에 노출하는 제공자입니다.
    `Service` 계층이 생략되었으므로, `Repository`를 직접 호출합니다.
    민감한 인증서 정보를 조회하는 작업 또한 중요한 보안 이벤트이므로,
    프로젝트의 아키텍처 패턴에 따라 자체적으로 감사 로그를 기록할 책임을 가집니다.
    """
    def get_certificate_by_serial(self, db: Session, *, serial_number: str, actor_user: Optional[User] = None) -> Optional[Dict]:
        """
        주어진 시리얼 번호에 해당하는 인증서의 상세 정보를 Vault에서 조회하고 감사 로그를 기록합니다.
        """
        logger.debug(f"Querying certificate details for serial number: {serial_number}")
        result = vault_certificate_query_repository.get_certificate_by_serial(serial_number)
        
        # 민감 정보 조회이므로 감사 로그 기록
        audit_command_provider.log(
            db=db,
            actor_user=actor_user,
            event_type="CERTIFICATE_VIEWED",
            description=f"Viewed certificate details for serial number: {serial_number}.",
            details={ "serial_number": serial_number }
        )
        return result

    def list_certificates_by_role(self, db: Session, *, role_name: str, actor_user: Optional[User] = None) -> List[str]:
        """
        특정 역할(role_name)로 발급된 모든 인증서의 시리얼 번호 목록을 Vault에서 조회하고 감사 로그를 기록합니다.
        """
        logger.debug(f"Listing certificates for role: {role_name}")
        result = vault_certificate_query_repository.list_certificates_by_role(role_name)

        # 민감 정보 목록 조회이므로 감사 로그 기록
        audit_command_provider.log(
            db=db,
            actor_user=actor_user,
            event_type="CERTIFICATES_LISTED",
            description=f"Listed certificates for role: {role_name}.",
            details={ "role_name": role_name }
        )
        return result

    def get_crl(self, db: Session, *, actor_user: Optional[User] = None) -> str:
        """
        Vault의 현재 유효한 인증서 폐기 목록(CRL)을 PEM 형식 문자열로 가져오고 감사 로그를 기록합니다.
        """
        logger.debug("Getting CRL from Vault")
        result = vault_certificate_query_repository.get_crl()
        # 민감 정보 조회이므로 감사 로그 기록
        audit_command_provider.log(
            db=db,
            actor_user=actor_user,
            event_type="CRL_VIEWED",
            description="Viewed Certificate Revocation List (CRL).",
            details={}
        )
        return result

    # get_valid_server_certificate는 Policy에서 이 Provider의 여러 메서드를 조합하여 구현될 것입니다.

certificate_query_provider = CertificateQueryProvider()