import logging
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.objects.user import User
from app.models.objects.role import Role
from app.models.objects.permission import Permission
from app.domains.inter_domain.role_management.schemas.role_command import PermissionAssignment
from app.domains.inter_domain.validators.permission.locked_permission_validator_provider import locked_permission_validator_provider
from app.domains.inter_domain.audit.audit_command_provider import audit_command_provider
from app.domains.inter_domain.role_management.role_command_provider import role_command_provider

logger = logging.getLogger(__name__)

class UpdateRolePermissionsPolicy:
    def execute(
        self, 
        db: Session, 
        *, 
        actor_user: User, 
        target_role_id: int, 
        permissions_in: List[PermissionAssignment],
        x_organization_id: Optional[int]
    ) -> None:
        """
        역할 권한 업데이트를 위한 정책을 실행합니다. 
        Ares Aegis: 검증 -> 수행 -> 로그 -> 커밋 순서를 트랜잭션 블록 내에서 엄격히 준수합니다.
        """
        try:
            # 1. 대상 역할 조회
            target_role = db.query(Role).options(joinedload(Role.permissions)).filter(Role.id == target_role_id).first()
            if not target_role:
                raise NotFoundError("Role", str(target_role_id))

            # 2. 규칙: 보호된 역할 (tier 0, 1) 수정 금지
            if target_role.tier is not None and target_role.tier < 2:
                raise PermissionDeniedError(f"Protected role '{target_role.name}' (tier {target_role.tier}) cannot be modified.")
            
            # 3. 규칙: 조직 교차 접근 방지
            if target_role.scope == "ORGANIZATION" and target_role.organization_id != x_organization_id:
                raise PermissionDeniedError("You cannot modify roles outside your current organization context.")

            # 4. 규칙: 시스템 잠금 권한 수정/제거 방지
            current_permission_ids = {rp.permission_id for rp in target_role.permissions}
            requested_permission_ids = {p.permission_id for p in permissions_in}
            
            changed_ids = current_permission_ids.symmetric_difference(requested_permission_ids)
            if changed_ids:
                changed_permissions = db.query(Permission).filter(Permission.id.in_(changed_ids)).all()
                locked_permission_validator_provider.validate(changed_permissions=changed_permissions)

            # 5. [Ares Aegis 핵심] 부분집합 원칙 검증
            # 5a. 행위자의 권한 세트 구성
            actor_permissions_set = set()
            for assignment in actor_user.user_role_assignments:
                is_system = assignment.role.scope == 'SYSTEM'
                is_valid_org = (assignment.role.scope == 'ORGANIZATION' and 
                                assignment.organization_id == x_organization_id)
                
                if is_system or is_valid_org:
                    for rp in assignment.role.permissions:
                        actor_permissions_set.add(rp.permission.name)

            # 5b. 요청된 권한 검증
            if requested_permission_ids:
                perms_from_db = db.query(Permission).filter(Permission.id.in_(requested_permission_ids)).all()
                if len(perms_from_db) != len(requested_permission_ids):
                    raise NotFoundError("Permission", "One or more requested IDs do not exist.")
                
                requested_names = {p.name for p in perms_from_db}

                # 5c. 권한 부여 자격 확인 (자신이 가진 권한만 남에게 줄 수 있음)
                if not requested_names.issubset(actor_permissions_set):
                    missing = requested_names - actor_permissions_set
                    raise PermissionDeniedError(f"You cannot grant permissions you do not possess: {', '.join(missing)}")

            # 6. [Command 수행] 실제 매핑 업데이트
            role_command_provider.update_role_permissions(
                db, 
                target_role=target_role, 
                permissions_in=permissions_in,
                actor_user=actor_user
            )
                        
            # 7. [Ares Aegis] 감사 로그 기록
            audit_command_provider.log(
                db=db,
                event_type="ROLE_PERMISSIONS_UPDATED",
                description=f"Permissions updated for role '{target_role.name}' (ID: {target_role_id})",
                actor_user=actor_user,
                details={
                    "target_role_id": target_role_id,
                    "role_name": target_role.name,
                    "assigned_permission_ids": list(requested_permission_ids),
                    "org_context": x_organization_id
                }
            )

            # 8. 최종 트랜잭션 커밋 (수행과 로그가 모두 성공했을 때만 데이터 확정)
            db.commit()
            logger.info(f"Policy: Permissions for role {target_role_id} updated and committed.")

        except Exception as e:
            # [Ares Aegis 핵심] 검증 실패부터 로그 기록 실패까지 모든 예외 상황에서 롤백
            db.rollback()
            logger.error(f"Policy Permission Update Failure for role {target_role_id}: {str(e)}")
            # 상위 엔드포인트(roles.py)가 대응할 수 있도록 예외 재발생
            raise e

update_role_permissions_policy = UpdateRolePermissionsPolicy()