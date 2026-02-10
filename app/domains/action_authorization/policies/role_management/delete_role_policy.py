import logging
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, ConflictError
from app.models.objects.user import User
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider
from app.domains.inter_domain.role_management.role_command_provider import role_command_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class DeleteRolePolicy:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        role_id: int
    ) -> None:
        """
        역할 삭제를 위한 정책을 실행합니다.
        Ares Aegis: 보호된 역할 보호 및 사용 중인 역할 삭제 방지를 강제하며 트랜잭션을 완결합니다.
        """
        try:
            # 1. 대상 역할 조회
            target_role = role_query_provider.get_role(db, role_id=role_id)
            if not target_role:
                # 역할이 없는 경우 API 계층에서 404를 던지도록 정책에서는 조용히 리턴
                return

            # --- [검증 단계] ---

            # 규칙 1: 보호된 역할 (tier 0, 1) 삭제 금지
            if target_role.tier is not None and target_role.tier < 2:
                raise ForbiddenError(f"Protected role '{target_role.name}' (tier {target_role.tier}) cannot be deleted.")

            # 규칙 2: 사용 중인 역할 삭제 금지 (연결된 사용자가 있는지 확인)
            if target_role.users:
                raise ConflictError(f"Role '{target_role.name}' is currently assigned to user(s) and cannot be deleted.")
            
            # --- [수행 및 기록 단계] ---

            # [Ares Aegis] 삭제될 데이터의 정보를 미리 스냅샷으로 저장 (로그용)
            deleted_role_name = target_role.name

            # 규칙 3: 역할 삭제 명령 수행
            role_command_provider.delete_role(db, db_obj=target_role)
            
            # 규칙 4: 감사 로그 기록 (수행과 한 트랜잭션으로 묶임)
            audit_command_provider.log(
                db=db,
                event_type="ROLE_DELETED",
                description=f"Role '{deleted_role_name}' (ID: {role_id}) deleted by {actor_user.username}",
                actor_user=actor_user,
                details={"role_id": role_id, "role_name": deleted_role_name}
            )
            
            # 규칙 5: 최종 트랜잭션 커밋
            db.commit()
            logger.info(f"Policy: Role {role_id} deleted successfully.")

        except Exception as e:
            # [Ares Aegis 핵심] 삭제 중 어떤 이유로든 실패 시 롤백
            db.rollback()
            logger.error(f"Policy Delete Failure for role {role_id}: {str(e)}")
            # 상위 엔드포인트로 예외를 전파하여 에러 응답을 생성하게 함
            raise e

delete_role_policy = DeleteRolePolicy()