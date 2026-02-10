import logging
from sqlalchemy.orm import Session
from typing import Optional

from app.core.exceptions import ForbiddenError
from app.models.objects.user import User
# Inter-Domain Provider
from app.domains.inter_domain.role_management.role_query_provider import role_query_provider
from app.domains.inter_domain.role_management.role_command_provider import role_command_provider
from app.domains.inter_domain.role_management.schemas.role_command import RoleUpdate
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider

logger = logging.getLogger(__name__)

class UpdateRolePolicy:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        role_id: int,
        role_in: RoleUpdate
    ) -> None:
        """
        역할 수정을 위한 정책을 실행합니다.
        Ares Aegis: 검증, 수행, 로그 기록을 하나의 트랜잭션으로 묶어 원자성을 보장합니다.
        """
        try:
            # 1. 대상 역할 조회
            target_role = role_query_provider.get_role(db, role_id=role_id)
            if not target_role:
                return # NotFound 처리는 엔드포인트에서 담당

            # [Ares Aegis] 변경 전 데이터 스냅샷 (로그용)
            old_values = {
                "name": target_role.name,
                "tier": target_role.tier,
                "description": target_role.description
            }

            # --- [검증 단계] ---

            # 규칙 1: API를 통해 역할을 보호 등급(0, 1)으로 승격 차단
            if role_in.tier is not None and role_in.tier < 2:
                if role_in.tier != target_role.tier:
                    raise ForbiddenError("Cannot set or change role tier to a protected level (0 or 1).")

            # 규칙 2: 이미 보호된 역할(tier 0, 1)인 경우 변경 제한
            is_protected = target_role.tier is not None and target_role.tier < 2
            if is_protected:
                if role_in.name is not None and role_in.name != target_role.name:
                    raise ForbiddenError(f"Name of protected role '{target_role.name}' cannot be changed.")
                
                if role_in.tier is not None and role_in.tier != target_role.tier:
                    raise ForbiddenError(f"Tier of protected role '{target_role.name}' cannot be changed.")

            # --- [수행 및 기록 단계] ---

            # 2. [Command] 실제 역할 수정 수행
            updated_role = role_command_provider.update_role(db, db_obj=target_role, obj_in=role_in)

            # 3. [Audit] 감사 로그 기록
            audit_command_provider.log(
                db=db,
                event_type="ROLE_UPDATED",
                description=f"Role '{target_role.name}' (ID: {role_id}) updated by {actor_user.username}",
                actor_user=actor_user,
                details={
                    "role_id": role_id,
                    "old_values": old_values,
                    "new_values": role_in.model_dump(exclude_unset=True)
                }
            )

            # 4. 최종 트랜잭션 커밋 (수정과 로그가 함께 확정됨)
            db.commit()
            return updated_role

        except Exception as e:
            # [Ares Aegis 핵심] 어떤 단계에서든 에러 발생 시 전체 롤백
            db.rollback()
            logger.error(f"Policy Update Failure for role {role_id}: {str(e)}")
            raise e

update_role_policy = UpdateRolePolicy()