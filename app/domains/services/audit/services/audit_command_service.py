# app/domains/services/audit/services/audit_command_service.py
from typing import Dict, List, Optional, Any
import json

from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.models.objects.device import Device
from app.models.events_logs.audit_log import AuditLog
from ..crud.audit_command_crud import audit_command_crud  # ← create_with_details 사용
from ..schemas.audit_command import AuditLogCreate, AuditLogDetailCreate


class AuditCommandService:
    """감사 로그 생성과 관련된 비즈니스 로직을 담당하는 서비스 클래스입니다."""

    def _infer_detail_type(self, value: Any) -> str:
        if isinstance(value, int):
            return "INTEGER"
        if isinstance(value, float):
            return "FLOAT"
        if isinstance(value, bool):
            return "BOOLEAN"
        if isinstance(value, (dict, list)):
            return "JSON"
        return "STRING"

    def _convert_dict_to_audit_details(self, data: Dict[str, Any], prefix: str = "") -> List[AuditLogDetailCreate]:
        detail_items: List[AuditLogDetailCreate] = []
        for key, value in data.items():
            detail_key = f"{prefix}{key}" if prefix else key
            detail_value_type = self._infer_detail_type(value)
            
            if detail_value_type == "JSON":
                detail_items.append(AuditLogDetailCreate(
                    detail_key=detail_key,
                    detail_value=json.dumps(value, ensure_ascii=False),
                    detail_value_type=detail_value_type
                ))
            else:
                detail_items.append(AuditLogDetailCreate(
                    detail_key=detail_key,
                    detail_value=str(value),
                    detail_value_type=detail_value_type
                ))
        return detail_items

    def log_creation(
        self, 
        db: Session, 
        *, 
        actor_user: Optional[User], 
        resource_name: str, 
        resource_id: int, 
        new_value: Dict[str, Any]
    ) -> AuditLog:
        details = self._convert_dict_to_audit_details(new_value, prefix="new_")
        details.insert(0, AuditLogDetailCreate(detail_key="resource_name", detail_value=resource_name, detail_value_type="STRING"))
        details.insert(1, AuditLogDetailCreate(detail_key="resource_id", detail_value=str(resource_id), detail_value_type="INTEGER"))

        audit_log_in = AuditLogCreate(
            event_type="RESOURCE_CREATED",
            log_level="INFO",
            description=f"{resource_name} (ID: {resource_id}) created.",
            user_id=actor_user.id if actor_user else None,
            details=details
        )

        # ← 수정됨: 최적화된 메서드 사용 (N+1 해결 + flush 불필요)
        return audit_command_crud.create_with_details(
            db=db,
            obj_in=audit_log_in,
            actor_user_id=actor_user.id if actor_user else None
        )

    def log_update(
        self, 
        db: Session, 
        *, 
        actor_user: Optional[User], 
        resource_name: str, 
        resource_id: int, 
        old_value: Dict[str, Any], 
        new_value: Dict[str, Any]
    ) -> AuditLog:
        details = self._convert_dict_to_audit_details(old_value, prefix="old_")
        details.extend(self._convert_dict_to_audit_details(new_value, prefix="new_"))
        details.insert(0, AuditLogDetailCreate(detail_key="resource_name", detail_value=resource_name, detail_value_type="STRING"))
        details.insert(1, AuditLogDetailCreate(detail_key="resource_id", detail_value=str(resource_id), detail_value_type="INTEGER"))

        audit_log_in = AuditLogCreate(
            event_type="RESOURCE_UPDATED",
            log_level="INFO",
            description=f"{resource_name} (ID: {resource_id}) updated.",
            user_id=actor_user.id if actor_user else None,
            details=details
        )

        # ← 수정됨: 기존 create() → create_with_details()로 변경
        #     더 이상 db.flush() 필요 없음 (CRUD 내부에서 처리)
        return audit_command_crud.create_with_details(
            db=db,
            obj_in=audit_log_in,
            actor_user_id=actor_user.id if actor_user else None
        )

    def log_deletion(
        self, 
        db: Session, 
        *, 
        actor_user: Optional[User], 
        resource_name: str, 
        resource_id: int, 
        deleted_value: Dict[str, Any]
    ) -> AuditLog:
        details = self._convert_dict_to_audit_details(deleted_value, prefix="deleted_")
        details.insert(0, AuditLogDetailCreate(detail_key="resource_name", detail_value=resource_name, detail_value_type="STRING"))
        details.insert(1, AuditLogDetailCreate(detail_key="resource_id", detail_value=str(resource_id), detail_value_type="INTEGER"))

        audit_log_in = AuditLogCreate(
            event_type="RESOURCE_DELETED",
            log_level="INFO",
            description=f"{resource_name} (ID: {resource_id}) deleted.",
            user_id=actor_user.id if actor_user else None,
            details=details
        )

        return audit_command_crud.create_with_details(
            db=db,
            obj_in=audit_log_in,
            actor_user_id=actor_user.id if actor_user else None
        )

    def log(
        self,
        db: Session,
        event_type: str,
        description: Optional[str],
        actor_user: Optional[User],
        target_user: Optional[User] = None,
        target_device: Optional[Device] = None,
        details: Optional[Dict[str, Any]] = None,
        log_level: Optional[str] = "INFO"
    ) -> AuditLog:
        """Creates a generic audit log entry."""
        if details:
            detail_items = self._convert_dict_to_audit_details(details)
        else:
            detail_items = []

        audit_log_in = AuditLogCreate(
            event_type=event_type,
            log_level=log_level.upper() if log_level else "INFO",
            description=description,
            user_id=actor_user.id if actor_user else None,
            target_user_id=target_user.id if target_user else None,
            target_device_id=target_device.id if target_device else None,
            details=detail_items
        )
        return audit_command_crud.create_with_details(
            db=db,
            obj_in=audit_log_in,
            actor_user_id=actor_user.id if actor_user else None
        )

    # 필요시 추가: log_custom_event() 등 자유롭게 확장 가능


audit_command_service = AuditCommandService()