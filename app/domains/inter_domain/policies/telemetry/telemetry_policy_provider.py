from sqlalchemy.orm import Session
from typing import List, Any
from app.models.objects.user import User
from app.domains.action_authorization.policies.telemetry_query.policy import telemetry_query_policy
from app.domains.services.telemetry.schemas.telemetry_query import TelemetryFilter

class TelemetryPolicyProvider:
    """
    [Inter-Domain Provider] 
    텔레메트리 조회 정책을 외부(API 등)에서 사용할 수 있도록 제공하는 통합 창구입니다.
    """

    def fetch_data(
        self, db: Session, *, actor_user: User, filters: TelemetryFilter, active_role_id: int
    ) -> List[Any]:
        """
        RBAC 기반의 텔레메트리 조회 정책을 실행합니다.
        관리자 권한 확인 및 일반 사용자의 소유 기간 필터링 오케스트레이션을 수행합니다.
        """
        return telemetry_query_policy.fetch_telemetry_data(
            db=db,
            actor_user=actor_user,
            filters=filters,
            active_role_id=active_role_id
        )

# 싱글톤 인스턴스
telemetry_policy_provider = TelemetryPolicyProvider()