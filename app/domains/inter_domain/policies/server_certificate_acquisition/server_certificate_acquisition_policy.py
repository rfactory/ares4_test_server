from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.domains.action_authorization.policies.server_certificate_acquisition.server_certificate_acquisition_policy import server_certificate_acquisition_policy

class ServerCertificateAcquisitionPolicyProvider:
    """
    `server_certificate_acquisition` policy의 기능을 외부 도메인에 노출하는 제공자입니다.
    `Policy`를 직접 호출합니다.
    """
    def acquire_valid_server_certificate(self, db: Session, current_cert_data: Optional[Dict]) -> Dict:
        """
        서버가 사용할 유효한 클라이언트 인증서를 획득합니다。
        """
        return server_certificate_acquisition_policy.acquire_valid_server_certificate(db, current_cert_data)

server_certificate_acquisition_policy_provider = ServerCertificateAcquisitionPolicyProvider()