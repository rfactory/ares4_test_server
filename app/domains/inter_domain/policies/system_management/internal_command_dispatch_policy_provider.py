from sqlalchemy.orm import Session
from typing import Dict, Any

# 실제 정책(Policy) 지휘관 임포트
from app.domains.action_authorization.policies.system_management.internal_command_dispatch_policy import internal_command_dispatch_policy

class InternalCommandDispatchPolicyProvider:
    """
    [Inter-Domain Provider] 
    내부 명령 발행 정책(Policy)에 대한 전용 인터페이스입니다.
    API 계층은 이 프로바이더를 통해서만 정책을 실행합니다.
    """
    
    def execute(self, db: Session, *, topic: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        내부 MQTT 명령 발행 정책을 대리 실행합니다.
        (Ares Aegis: 정책 내부에서 시스템 액터 식별, 감사 로그, 트랜잭션 완결 수행)
        """
        return internal_command_dispatch_policy.execute(
            db, 
            topic=topic, 
            command=command
        )

# 전역에서 사용할 싱글톤 인스턴스
internal_command_dispatch_policy_provider = InternalCommandDispatchPolicyProvider()