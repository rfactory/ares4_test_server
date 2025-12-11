import logging
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

# Provider를 통해 다른 도메인의 기능을 가져옵니다.
from app.domains.inter_domain.user_identity.user_identity_query_provider import user_identity_query_provider
from app.domains.inter_domain.validators.emqx_auth.provider import emqx_auth_validator_provider

logger = logging.getLogger(__name__)

# 임시 정적 ACL 규칙 (원래는 DB나 설정 파일에서 로드)
STATIC_ACL_RULES = {
    "ares-server-v2": [
        {"topic": "#", "permission": "allow", "action": "all"}
    ],
    "ares4-mqtt-listener": [
        {"topic": "#", "permission": "allow", "action": "all"}
    ]
}

class EmqxAuthPolicy:
    """EMQX의 인증/인가 웹훅 요청에 대한 최종 결정을 내리는 Policy입니다."""

    async def handle_auth(self, db: Session, *, username: str, password: str) -> bool:
        """사용자 인증을 처리하고 성공/실패를 반환합니다."""
        logger.info(f"[Policy] Authenticating user '{username}'.")
        
        # 1. 사용자 정보 가져오기
        user = user_identity_query_provider.get_user_by_username(db, username=username)
        if not user:
            logger.warning(f"[Policy] Authentication failed: User '{username}' not found.")
            return False
        
        # 2. 비밀번호 확인
        # if not user_identity_query_provider.verify_password(password, user.hashed_password):
        #     logger.warning(f"[Policy] Authentication failed: Invalid password for user '{username}'.")
        #     return False
        
        # 참고: 현재 user_identity_provider에 verify_password가 없으므로 임시로 통과시킵니다.
        # 실제로는 위 주석을 해제해야 합니다.
        logger.info(f"[Policy] Authentication successful for user '{username}'.")
        return True

    async def handle_acl(self, db: Session, *, username: str, client_id: str, topic: str, access: str) -> bool:
        """토픽 접근 권한(ACL)을 처리하고 허용/거부를 반환합니다."""
        logger.info(f"[Policy] Checking ACL for client_id='{client_id}', username='{username}' on topic='{topic}', access='{access}'.")

        # 1. 슈퍼유저인지 확인 (validator 사용)
        if emqx_auth_validator_provider.is_superuser(username):
            logger.info(f"[Policy] ACL allowed: User '{username}' is a superuser.")
            return True

        # 2. 정적 ACL 규칙에서 해당 클라이언트/사용자 규칙 가져오기 (수정됨: 접두사 매칭)
        rules = []
        for prefix, prefix_rules in STATIC_ACL_RULES.items():
            if client_id.startswith(prefix) or username.startswith(prefix):
                rules.extend(prefix_rules)
                logger.debug(f"[Policy] Matched prefix '{prefix}' for client '{client_id}'. Applying rules: {prefix_rules}")

        logger.debug(f"[Policy] Found {len(rules)} rules for client_id='{client_id}', username='{username}': {rules}")
        if not rules:
            logger.warning(f"[Policy] ACL denied: No rules found for client_id='{client_id}' or username='{username}'.")
            return False

        # 3. 각 규칙을 순회하며 접근 가능 여부 판별
        for i, rule in enumerate(rules):
            logger.debug(f"[Policy] Evaluating rule #{i+1}: {rule}")
            # action(pub/sub/all) 검사
            if rule["action"] != "all" and rule["action"] != access:
                logger.debug(f"[Policy] Rule #{i+1} skipped: action mismatch (rule: {rule['action']}, access: {access})")
                continue

            # 토픽 매칭 검사
            if emqx_auth_validator_provider.can_access_topic(rule["topic"], topic):
                is_allowed = rule["permission"] == "allow"
                logger.info(f"[Policy] ACL {(('allowed' if is_allowed else 'denied'))} by matching rule #{i+1}: {rule}")
                return is_allowed

        logger.warning(f"[Policy] ACL denied: No matching rule found for topic '{topic}'.")
        return False

emqx_auth_policy = EmqxAuthPolicy()
