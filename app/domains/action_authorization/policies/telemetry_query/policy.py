import logging
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.objects.user import User
from app.core.exceptions import AccessDeniedError
from app.domains.inter_domain.system_unit_assignment.system_unit_assignment_query_provider import system_unit_assignment_query_provider
from app.domains.inter_domain.telemetry.telemetry_query_provider import telemetry_query_provider
from app.domains.inter_domain.permissions.permission_query_provider import permission_query_provider
from app.domains.services.telemetry.schemas.telemetry_query import TelemetryFilter
from app.models.events_logs.telemetry_data import TelemetryData

logger = logging.getLogger(__name__)

class TelemetryQueryPolicy:
    """
    [The Harmonizer - 시나리오 A 및 데이터 정직성 정책]
    
    1. 일반 사용자: 본인이 유닛을 소유했던 기간(assigned_at ~ unassigned_at)의 데이터만 조회 가능.
    2. 관리자: 전체 이력 조회 권한이 있다면 모든 기간의 데이터 조회 가능.
    3. 데이터 불변성: 이 정책은 오직 '읽기'만을 수행하며, 텔레메트리 도메인 내의 삭제/임의 생성 로직은 배제됨.
    """
        
    def fetch_telemetry_data(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        filters: TelemetryFilter, 
        active_role_id: int
    ) -> List[TelemetryData]:
        """
        권한 및 역할 기반 텔레메트리 조회 오케스트레이션.
        """
        # 1. [RBAC 체크] 현재 활성화된 Role이 'telemetry:read_all' 권한을 가졌는지 확인
        # (시딩 스크립트 ESSENTIAL_PERMISSIONS에 정의된 키를 직접 사용)
        is_privileged_role = permission_query_provider.check_role_has_permission(
            db, role_id=active_role_id, permission_name="telemetry:read_all"
        )

        possession_start = None
        possession_end = None

        # 2. 전역 권한이 없는 일반 Role일 경우: 시나리오 A(기간 격리) 적용
        if not is_privileged_role:
            if not filters.system_unit_ids:
                raise AccessDeniedError("일반 사용자는 조회할 시스템 유닛 ID를 명시해야 합니다.")

            unit_id = filters.system_unit_ids[0]
            
            # 해당 유저가 이 유닛을 소유했던 기록을 가져옴
            assignment = system_unit_assignment_query_provider.get_assignment_period(
                db, unit_id=unit_id, user_id=actor_user.id
            )

            if not assignment:
                logger.warning(f"Access Denied: User {actor_user.id} -> Unit {unit_id}")
                return [] 

            # 소유 시작 시점과 종료 시점(unassigned_at)을 확보하여 필터로 사용
            possession_start = assignment.created_at
            possession_end = assignment.unassigned_at

        # 3. Telemetry Provider 호출
        # possession 정보가 있으면 필터링이 수행되고, None(관리자 권한)이면 전체 조회가 수행됩니다.
        return telemetry_query_provider.get_telemetry_data(
            db=db,
            filters=filters,
            possession_start=possession_start,
            possession_end=possession_end
        )

telemetry_query_policy = TelemetryQueryPolicy()