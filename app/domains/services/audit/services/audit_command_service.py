from typing import Dict, List, Optional, Any
import json
import logging

from sqlalchemy.orm import Session

from app.models.objects.user import User
from app.models.objects.device import Device
from app.models.events_logs.audit_log import AuditLog
from ..crud.audit_command_crud import audit_command_crud
from ..schemas.audit_command import AuditLogCreate, AuditLogDetailCreate

logger = logging.getLogger(__name__)

class AuditCommandService:
    """
    감사 로그 생성과 관련된 비즈니스 로직을 담당하는 서비스 클래스입니다.
    DB Enum(audit_log_event_type)에 정의된 값만 사용하도록 엄격히 제한하여 롤백을 방지합니다.
    """
    
    # 1. DB에서 확인된 실제 허용 단어 목록 (화이트리스트)
    SAFE_EVENT_TYPES = [
        "DEVICE", "AUDIT", "CONSUMABLE_USAGE", "SERVER_MQTT_CERTIFICATE_ISSUED",
        "DEVICE_CERTIFICATE_CREATED", "CERTIFICATE_REVOKED", 
        "SERVER_CERTIFICATE_ACQUIRED_NEW", "SERVER_CERTIFICATE_REUSED",
        "ORGANIZATION_CREATED", "ORGANIZATION_UPDATED", "ORGANIZATION_DELETED",
        "ACCESS_REQUEST_CREATED", "ACCESS_REQUEST_UPDATED", "ACCESS_REQUEST_DELETED",
        "USER_ROLE_ASSIGNED", "USER_ROLE_REVOKED", "USER_LOGIN_FAILED",
        "MQTT_AUTH_SUCCESS", "MQTT_AUTH_FAILURE",
        "SYSTEM_UNIT_BIND_SUCCESS", "SYSTEM_UNIT_CLAIM_SUCCESS", "DEVICE_REROUTED",
    ]

    def _get_safe_event_type(self, event_type: str) -> str:
        """전달된 event_type을 DB가 허용하는 Enum 값으로 강제 변환합니다."""
        upper_type = event_type.upper()
        
        # 이미 목록에 있는 정석 단어라면 그대로 반환
        if upper_type in self.SAFE_EVENT_TYPES:
            return upper_type
            
        # [매핑 로직] DB에 없는 단어(INFO, RESOURCE_CREATED 등)를 DB용 단어로 번역
        # 인증서 관련
        if "CERTIFICATE" in upper_type:
            if "ISSUED" in upper_type or "CREATED" in upper_type:
                return "SERVER_MQTT_CERTIFICATE_ISSUED"
            return "SERVER_CERTIFICATE_ACQUIRED_NEW"
            
        # 조직 관련
        if "ORGANIZATION" in upper_type:
            if "CREATE" in upper_type: return "ORGANIZATION_CREATED"
            if "DELETE" in upper_type: return "ORGANIZATION_DELETED"
            return "ORGANIZATION_UPDATED"

        # 기기 및 공장 등록 관련
        if "DEVICE" in upper_type or "RESOURCE" in upper_type or "FACTORY" in upper_type:
            return "DEVICE"

        # 로그인 및 권한 관련
        if "AUTH" in upper_type:
            return "MQTT_AUTH_SUCCESS" if "SUCCESS" in upper_type else "MQTT_AUTH_FAILURE"
        if "LOGIN" in upper_type:
            return "USER_LOGIN_FAILED"

        # 그 외 모든 알 수 없는 타입 (INFO 포함)
        return "AUDIT"

    def _infer_detail_type(self, value: Any) -> str:
        """데이터 값에 따른 DB 저장 타입을 추론합니다."""
        if isinstance(value, int): return "INTEGER"
        if isinstance(value, float): return "FLOAT"
        if isinstance(value, bool): return "BOOLEAN"
        if isinstance(value, (dict, list)): return "JSON"
        return "STRING"

    def _convert_dict_to_audit_details(self, data: Dict[str, Any], prefix: str = "") -> List[AuditLogDetailCreate]:
        """딕셔너리 데이터를 AuditLog 상세 항목 리스트로 변환합니다."""
        detail_items: List[AuditLogDetailCreate] = []
        for key, value in data.items():
            detail_key = f"{prefix}{key}" if prefix else key
            detail_value_type = self._infer_detail_type(value)
            
            val_str = json.dumps(value, ensure_ascii=False) if detail_value_type == "JSON" else str(value)
            detail_items.append(AuditLogDetailCreate(
                detail_key=detail_key,
                detail_value=val_str,
                detail_value_type=detail_value_type
            ))
        return detail_items

    def _get_actor_id(self, db: Session, actor_user: Optional[User]) -> int:
        """
        행위자 ID 결정: 유저가 있으면 그 ID를, 없으면 DB에서 'ares_user'를 찾아 반환합니다.
        """
        if actor_user:
            return actor_user.id
            
        # ✅ [수정] ID=1 하드코딩 대신 'ares_user' 조회
        system_user = db.query(User).filter(User.username == "ares_user").first()
        
        if system_user:
            return system_user.id
            
        # 최후의 보루: 시스템 유저가 DB에 아예 없을 경우 (시딩 실패 대비)
        logger.warning("System user 'ares_user' not found in DB. Falling back to ID 1.")
        return 1

    # --- 실질적인 로그 생성 메서드들 ---

    def log_creation(self, db: Session, *, actor_user: Optional[User], resource_name: str, resource_id: int, new_value: Dict[str, Any]) -> AuditLog:
        """리소스 생성 로그 (기존 상세 로직 유지)"""
        details = self._convert_dict_to_audit_details(new_value, prefix="new_")
        details.insert(0, AuditLogDetailCreate(detail_key="resource_name", detail_value=resource_name, detail_value_type="STRING"))
        details.insert(1, AuditLogDetailCreate(detail_key="resource_id", detail_value=str(resource_id), detail_value_type="INTEGER"))

        return self.log(
            db=db,
            event_type="DEVICE" if resource_name.lower() == "device" else "AUDIT",
            description=f"{resource_name} (ID: {resource_id}) created.",
            actor_user=actor_user,
            details_as_list=details # 가공된 리스트 직접 전달
        )

    def log_update(self, db: Session, *, actor_user: Optional[User], resource_name: str, resource_id: int, old_value: Dict[str, Any], new_value: Dict[str, Any]) -> AuditLog:
        """리소스 수정 로그 (이전/이후 값 모두 추적)"""
        details = self._convert_dict_to_audit_details(old_value, prefix="old_")
        details.extend(self._convert_dict_to_audit_details(new_value, prefix="new_"))
        details.insert(0, AuditLogDetailCreate(detail_key="resource_name", detail_value=resource_name, detail_value_type="STRING"))
        details.insert(1, AuditLogDetailCreate(detail_key="resource_id", detail_value=str(resource_id), detail_value_type="INTEGER"))

        return self.log(
            db=db,
            event_type="AUDIT",
            description=f"{resource_name} (ID: {resource_id}) updated.",
            actor_user=actor_user,
            details_as_list=details
        )

    def log_deletion(self, db: Session, *, actor_user: Optional[User], resource_name: str, resource_id: int, deleted_value: Dict[str, Any]) -> AuditLog:
        """리소스 삭제 로그"""
        details = self._convert_dict_to_audit_details(deleted_value, prefix="deleted_")
        details.insert(0, AuditLogDetailCreate(detail_key="resource_name", detail_value=resource_name, detail_value_type="STRING"))
        details.insert(1, AuditLogDetailCreate(detail_key="resource_id", detail_value=str(resource_id), detail_value_type="INTEGER"))

        return self.log(
            db=db,
            event_type="AUDIT",
            description=f"{resource_name} (ID: {resource_id}) deleted.",
            actor_user=actor_user,
            details_as_list=details
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
        details_as_list: Optional[List[AuditLogDetailCreate]] = None, # 리스트 직접 입력 대응
        log_level: Optional[str] = "INFO"
    ) -> AuditLog:
        """범용 감사 로그 생성기 (모든 로그의 종착역)"""
        actor_id = self._get_actor_id(db, actor_user)
        
        # 상세 항목 데이터 결정
        final_details = details_as_list if details_as_list else (self._convert_dict_to_audit_details(details) if details else [])

        # ✅ [핵심] DB가 거부하지 않도록 event_type 세탁
        safe_event_type = self._get_safe_event_type(event_type)

        audit_log_in = AuditLogCreate(
            event_type=safe_event_type,
            log_level=log_level.upper() if log_level else "INFO",
            description=description,
            user_id=actor_id,
            target_user_id=target_user.id if target_user else None,
            target_device_id=target_device.id if target_device else None,
            details=final_details
        )
        
        return audit_command_crud.create_with_details(
            db=db,
            obj_in=audit_log_in,
            actor_user_id=actor_id
        )
        
    def log_event(self, db: Session, event_type: str, description: str, details: Dict[str, Any], log_level: str = "INFO") -> AuditLog:
        """행위자 없는 시스템 자동 이벤트 기록"""
        return self.log(
            db=db,
            event_type=event_type,
            description=description,
            actor_user=None,
            details=details,
            log_level=log_level
        )

audit_command_service = AuditCommandService()