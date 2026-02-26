import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.core.exceptions import NotFoundError, AccessDeniedError
from app.domains.inter_domain.system_unit_assignment.system_unit_assignment_query_provider import system_unit_assignment_query_provider
from app.domains.inter_domain.system_unit_assignment.system_unit_assignment_command_provider import system_unit_assignment_command_provider
from app.domains.inter_domain.system_unit.system_unit_command_provider import system_unit_command_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.models.objects.user import User

logger = logging.getLogger(__name__)

class SystemUnitUnbindingPolicy:
    """
    [The Harmonizer - 시나리오 A]
    시스템 유닛과 사용자의 소유 관계를 물리적 삭제 없이 종료(Soft Unbind)합니다.
    기기 연결 정보와 핀맵은 유지하여 다음 사용자가 즉시 사용할 수 있게 합니다.
    """

    def unbind_owner(self, db: Session, *, actor_user: User, unit_id: int) -> Dict[str, Any]:
        try:
            # 1. 현재 활성화된 OWNER 할당 정보 조회
            assignment = system_unit_assignment_query_provider.get_active_owner_assignment(
                db, unit_id=unit_id, user_id=actor_user.id
            )
            
            if not assignment:
                raise AccessDeniedError("해당 유닛에 대한 소유권이 없거나 이미 해제되었습니다.")

            # 2. 소유권 종료 실행 (unassigned_at 업데이트)
            # 이 명령이 실행되면 모델의 before_update 리스너가 작동하여 
            # 이 주인이 초대했던 다른 사람들(Operator, Viewer)도 자동으로 종료됩니다.
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            system_unit_assignment_command_provider.terminate_assignment(
                db, assignment_id=assignment.id, unassigned_at=now
            )

            # 3. 유닛 상태 변경
            # 기기는 그대로 꽂혀있으므로 ACTIVE에서 PENDING_OWNER(새 주인 대기) 상태로 바꿉니다.
            system_unit_command_provider.update_unit_status(
                db, unit_id=unit_id, status="PROVISIONING", actor_user=actor_user
            )

            # 4. 결과 기록 (Audit Log)
            audit_command_provider.log_event(
                db=db,
                actor_user=actor_user,
                event_type="DEVICE_UNIT_UNBIND_SUCCESS",
                description=f"User {actor_user.id} released ownership of Unit {unit_id}. Data preserved.",
                details={"unit_id": unit_id, "terminated_at": now.isoformat()}
            )

            db.commit()
            logger.info(f"🔓 유닛 {unit_id} 소유권 해제 완료 (사용자: {actor_user.id})")
            return {"status": "success", "unit_id": unit_id, "released_at": now}

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Unbinding Policy Failure: {str(e)}")
            raise e

system_unit_unbinding_policy = SystemUnitUnbindingPolicy()