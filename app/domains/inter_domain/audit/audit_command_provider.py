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
    # 1. 범용 로그
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
    
    # 2. 리소스 생성 로그 (Service로 위임)
    def log_creation(
        self,
        db: Session,
        actor_user: Optional[User],
        resource_name: str,
        resource_id: int,
        new_value: Dict[str, Any]
    ) -> AuditLog:
        return audit_command_service.log_creation(
            db=db,
            actor_user=actor_user,
            resource_name=resource_name,
            resource_id=resource_id,
            new_value=new_value
        )
    
    # 3. 리소스 수정 로그 (Service로 위임)
    def log_update(
        self,
        db: Session,
        actor_user: Optional[User],
        resource_name: str,
        resource_id: int,
        old_value: Dict[str, Any],
        new_value: Dict[str, Any]
    ) -> AuditLog:
        return audit_command_service.log_update(
            db=db,
            actor_user=actor_user,
            resource_name=resource_name,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value
        )
    
    # 4. 리소스 삭제 로그 (Service로 위임)
    def log_deletion(
        self,
        db: Session,
        actor_user: Optional[User],
        resource_name: str,
        resource_id: int,
        deleted_value: Dict[str, Any]
    ) -> AuditLog:
        return audit_command_service.log_deletion(
            db=db,
            actor_user=actor_user,
            resource_name=resource_name,
            resource_id=resource_id,
            deleted_value=deleted_value
        )
        
    def log_event(
        self, 
        db: Session, 
        event_type: str, 
        description: str, 
        details: Dict[str, Any],
        log_level: str = "INFO"
    ) -> AuditLog:
        """
        Policy 계층에서 호출하는 범용 비즈니스 로그 인터페이스입니다.
        """
        return audit_command_service.log_event(
            db=db,
            event_type=event_type,
            description=description,
            details=details,
            log_level=log_level
        )
audit_command_provider = AuditCommandProvider()
