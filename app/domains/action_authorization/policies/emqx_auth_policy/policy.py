import logging
import re
from typing import Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session

# Inter-domain Provider들을 통해 각 도메인의 기능을 통합합니다.
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.device_management.device_query_provider import device_management_query_provider
from app.domains.inter_domain.validators.emqx_auth.provider import emqx_auth_validator_provider
from app.domains.inter_domain.validators.device_ownership.provider import device_ownership_validator_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.domains.inter_domain.validators.device_existence.provider import device_existence_validator_provider

logger = logging.getLogger(__name__)

# 시스템 내부 서비스용 정적 ACL 규칙
STATIC_ACL_RULES = {
    "ares-server-v2": [{"topic": "#", "permission": "allow", "action": "all"}],
    "ares4-mqtt-listener": [{"topic": "#", "permission": "allow", "action": "all"}],
    "ares_user": [{"topic": "ares4/#", "permission": "allow", "action": "all"}]
}

class EmqxAuthPolicy:
    """EMQX의 인증/인가 웹훅 요청에 대한 최종 결정을 내리는 Policy입니다."""

    async def handle_auth(self, db: Session, *, username: Optional[str] = None, password: Optional[str] = None, client_id: Optional[str] = None) -> bool:
        """사용자(ID/PW) 또는 기기(mTLS) 인증 시나리오를 지휘합니다."""
        
        # 1. 사용자 인증 루트 (아이디와 비밀번호가 모두 제공된 경우)
        if username and password:
            logger.info(f"[Policy] Path A: User Password Auth flow for '{username}'.")
            user = user_identity_query_provider.get_user_by_username(db, username=username)
            if not user:
                audit_command_provider.log(
                    db=db,
                    event_type="MQTT_AUTH_FAILED",
                    description=f"MQTT Auth failed: User '{username}' not found.",
                    actor_user=None,
                    details={"username_attempted": username}
                )
                db.commit()
                return False
            
            # (비밀번호 검증이 필요하다면 여기서 Validator를 추가로 지휘할 수 있습니다)
            audit_command_provider.log(
                db=db,
                event_type="MQTT_AUTH_SUCCESS",
                description=f"MQTT Auth successful for user '{username}'.",
                actor_user=user,
                details={"username": username}
            )
            db.commit()
            return True

        # 2. 기기 인증 루트 (mTLS 하이패스 - 패스워드 없이 client_id만 온 경우)
        if client_id:
            logger.info(f"[Policy] Path B: Orchestrating mTLS Auth for device: {client_id}")
            
            # [Step 1: Data Supply] 쿼리 전문가에게 데이터를 가져오라고 시킵니다.
            device = device_management_query_provider.get_device_by_identifier(db, identifier=client_id)
            
            # [Step 2: Validation] 판단 전문가(Validator Provider)에게 '이 기기가 통과될 만한지' 묻습니다.
            # (우리가 방금 수정한 '판단 전용' 메서드를 사용합니다)
            is_valid, error_msg = device_existence_validator_provider.validate_device_existence(device=device)
            
            if is_valid:
                # [Step 3: Action] 성공 시 감사 로그 기록을 지시하고 최종 승인합니다.
                audit_command_provider.log(
                    db=db,
                    event_type="MQTT_DEVICE_AUTH_SUCCESS",
                    description=f"MQTT Device Auth successful for ID '{client_id}'.",
                    actor_user=None,
                    details={"client_id": client_id}
                )
                db.commit()
                return True
            
            logger.warning(f"[Policy] Device Auth Rejected: {error_msg}")

        # 3. 모든 인증 루트 실패
        return False

    async def handle_acl(self, db: Session, *, username: str, client_id: str, topic: str, access: str) -> bool:
        """토픽 접근 권한(ACL)을 계층적으로 검증합니다."""
        logger.info(f"[Policy] Checking ACL: client_id='{client_id}', user='{username}', topic='{topic}'")

        # 1. 슈퍼유저 확인 (최우선순위)
        if emqx_auth_validator_provider.is_superuser(username):
            return True

        # 2. 정적 시스템 규칙 확인
        for prefix, rules in STATIC_ACL_RULES.items():
            if (client_id and client_id.startswith(prefix)) or (username and username.startswith(prefix)):
                for rule in rules:
                    if emqx_auth_validator_provider.can_access_topic(rule["topic"], topic):
                        return rule["permission"] == "allow"

        # 3. [동적 권한 검증] 장치 식별자 추출
        identifier = self._extract_identifier(topic)
        if not identifier:
            self._log_acl_denied(db, username, topic, access, "Malformed topic path: No device identifier")
            return False

        # 4. [Data Supply] 장치 정보 조회
        device = device_management_query_provider.get_device_by_identifier(db, identifier=identifier)
        if not device:
            self._log_acl_denied(db, username, topic, access, "Device not registered")
            return False

        # 5. [Business Logic] 소유권 검증 위임
        # username이 비어있다면 mTLS 기기로 간주하고, 
        # client_id가 해당 device의 식별자와 일치하는지만 확인하거나 승인하는 로직이 필요할 수 있습니다.
        if not username:
            # mTLS 기기는 자기 자신의 토픽에는 무조건 권한을 주는 식의 로직
            is_allowed = (identifier == client_id) 
            msg = "mTLS device self-access" if is_allowed else "Device ID mismatch"
        else:
            is_allowed, msg = device_ownership_validator_provider.validate_access(
                db, user_email=username, device=device, access=access
            )

        if is_allowed:
            return True
        
        self._log_acl_denied(db, username, topic, access, msg, device_id=device.id)
        return False
    
    def _log_acl_denied(self, db: Session, username: str, topic: str, access: str, reason: str, device_id: Optional[int] = None):
        """ACL 거부 로그 통합 관리"""
        user = user_identity_query_provider.get_user_by_username(db, username=username)
        audit_command_provider.log(
            db=db,
            event_type="MQTT_ACL_DENIED",
            description=f"MQTT ACL Denied for {username} on {topic} ({access}). Reason: {reason}",
            actor_user=user,
            details={"username": username, "topic": topic, "reason": reason, "device_id": device_id}
        )
        db.commit()
    
    def _extract_identifier(self, topic: str) -> Optional[str]:
        """토픽 경로에서 장치 식별자 추출"""
        match = re.search(r'ares4/([^/]+)', topic)
        return match.group(1) if match else None

# 싱글톤 인스턴스
emqx_auth_policy = EmqxAuthPolicy()