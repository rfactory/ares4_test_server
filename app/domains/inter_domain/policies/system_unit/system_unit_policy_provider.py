from sqlalchemy.orm import Session
from typing import Any, Dict
from app.models.objects.user import User

# 실제 비즈니스 로직(Policy) 임포트
from app.domains.action_authorization.policies.system_unit_binding.system_unit_binding_policy import system_unit_binding_policy
from app.domains.action_authorization.policies.system_unit_unbinding.policy import system_unit_unbinding_policy

class SystemUnitPolicyProvider:
    """
    [Inter-Domain Provider] 
    시스템 유닛 관련 정책들을 외부(API 등)에 제공하는 통합 창구입니다.
    """

    def bind_device(
        self, db: Session, *, actor_user: User, unit_id: int, device_id: int, role: str
    ) -> Any:
        """장치와 유닛 결합 정책 실행"""
        return system_unit_binding_policy.bind_device_to_unit(
            db=db, actor_user=actor_user, unit_id=unit_id, device_id=device_id, role=role
        )

    def unbind_owner(
        self, db: Session, *, actor_user: User, unit_id: int
    ) -> Dict[str, Any]:
        """소유권 해제 정책 실행"""
        return system_unit_unbinding_policy.unbind_owner(
            db=db, actor_user=actor_user, unit_id=unit_id
        )

# 싱글톤 인스턴스
system_unit_policy_provider = SystemUnitPolicyProvider()