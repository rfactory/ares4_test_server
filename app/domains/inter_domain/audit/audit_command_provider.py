from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.models.objects.device import Device
from app.models.events_logs.audit_log import AuditLog
from app.domains.services.audit.services.audit_command_service import audit_command_service

class AuditCommandProvider:
    """
    audit_management_service의 기능을 외부 도메인에 노출하는 제공자입니다.
    일관성을 위해 'Management' 대신 'Command'를 사용합니다.
    """
    def log(
        self, 
        db: Session,
        event_type: str, 
        description: Optional[str],
        actor_user: Optional[User], 
        target_user: Optional[User] = None,
        target_device: Optional[Device] = None,
        details: Optional[Dict[str, Any]] = None,
        log_level: Optional[str] = None
    ) -> AuditLog:
        """
        내부 audit_management_service를 호출하여 로그를 생성합니다.
        """
        return audit_command_service.log(
            db=db,
            event_type=event_type,
            description=description,
            actor_user=actor_user,
            target_user=target_user,
            target_device=target_device,
            details=details,
            log_level=log_level
        )

audit_command_provider = AuditCommandProvider()
